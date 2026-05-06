from time import time

import click
import djvu.decode
import loguru

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.images import ImageMode
from dpsprep.logging import configure_loguru, human_readable_size
from dpsprep.options import DpsPrepOptions, parse_ocr_options
from dpsprep.workdir import WorkingDirectory
from dpsprep.workflow import attempt_to_optimize_result, combine_document, process_in_pool


@click.option('--ocr', type=str, is_flag=False, flag_value='{}', help='Perform OCR via OCRmyPDF rather than trying to convert the text layer. If this parameter has a value, it should be a JSON dictionary of options to be passed to OCRmyPDF.')
@click.option('--dpi', type=click.IntRange(min=1), help='Override DPI values encoded in the DjVu file for individual pages.')
@click.option('-m', '--mode', type=click.Choice(['infer', 'bitonal', 'grayscale', 'rgb']), default='infer', help='Override the image modes encoded in the DjVu file for individual pages. It sometimes makes sense to force bitonal images since they compress well.')
@click.option('-q', '--quality', type=click.IntRange(min=0, max=100), help="Quality of images in output. Used only for JPEG compression, i.e. RGB and Grayscale images. Passed directly to Pillow and to OCRmyPDF's optimizer.")
@click.option('-p', '--pool-size', type=click.IntRange(min=0), default=4, help='Size of MultiProcessing pool for handling page-by-page operations.')
@click.option('-O3', 'optlevel', flag_value=3, help='Use the aggressive lossy PDF image optimization from OCRmyPDF.')
@click.option('-O2', 'optlevel', flag_value=2, help='Use the PDF image optimization from OCRmyPDF.')
@click.option('-O1', 'optlevel', flag_value=1, help='Use the lossless PDF image optimization from OCRmyPDF (without performing OCR).')
@click.option('-t', '--no-text', is_flag=True, help='Disable the generation of text layers. Implied by --ocr.')
@click.option('-v', '--verbose', is_flag=True, help='Display debug messages.')
@click.option('-o', '--overwrite', is_flag=True, help='Overwrite destination file.')
@click.option('-w', '--preserve-working', is_flag=True, help='Preserve the working directory after script termination.')
@click.option('-d', '--delete-working', is_flag=True, help='Delete any existing files in the working directory prior to writing to it.')
@click.version_option()
@click.argument('dest', type=click.Path(exists=False, resolve_path=True), required=False)
@click.argument('src', type=click.Path(exists=True, resolve_path=True), required=True)
@click.command(epilog='See dpsprep(1) for more details.')
def dpsprep(
    src: str,
    dest: str | None,
    delete_working: bool,
    preserve_working: bool,
    overwrite: bool,
    deprecated_overwrite: bool,
    verbose: bool,
    no_text: bool,
    optlevel: int | None,
    pool_size: int,
    quality: int | None,
    mode: ImageMode,
    dpi: int | None,
    ocr: str | None,
) -> None:
    """Convert DjVu files to PDF.

    The name comes from Sony's Digital Paper System (DPS), for which the tool was initially developed.
    """
    configure_loguru(verbose=verbose)

    try:
        ocr_options = parse_ocr_options(ocr)
    except DpsPrepConfigError as err:
        raise SystemExit(str(err)) from err

    if ocr_options:
        no_text = True

    options = DpsPrepOptions(
        dpi=dpi,
        mode=mode,
        no_text=no_text,
        ocr_options=ocr_options,
        optlevel=optlevel,
        pool_size=pool_size,
        quality=quality,
        verbose=verbose,
    )

    workdir = WorkingDirectory(src, dest)

    if not overwrite and workdir.dest.exists():
        raise SystemExit(f'File {workdir.dest} already exists.')

    start_time = time()

    if workdir.workdir.exists():
        if delete_working:
            loguru.logger.debug(f'Removing existing working directory {workdir.workdir}.')
            workdir.destroy()
            loguru.logger.info(f'Removed existing working directory {workdir.workdir}.')
        else:
            loguru.logger.info(f'Reusing working directory {workdir.workdir}.')
    else:
        loguru.logger.info(f'Working directory {workdir.workdir} has been created.')

    workdir.create_if_necessary()

    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src),
    )
    document.decoding_job.wait()
    djvu_size = workdir.src.stat().st_size

    process_in_pool(workdir, options, document)
    combine_document(workdir, options, document)

    combined_size = workdir.combined_pdf_path.stat().st_size
    loguru.logger.info(f'Produced a combined output file with size {human_readable_size(combined_size)} in {time() - start_time:.2f}s. This is {round(100 * combined_size / djvu_size, 2)}% of the DjVu source file.')

    attempt_to_optimize_result(workdir, options, djvu_size, combined_size)

    if preserve_working:
        loguru.logger.info(f'Working directory {workdir.workdir} will be preserved.')
    else:
        loguru.logger.info(f'Deleting the working directory {workdir.workdir}.')
        workdir.destroy()
