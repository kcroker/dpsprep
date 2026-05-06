from time import time

import click
import djvu.decode
import loguru

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.logging import configure_loguru, human_readable_size
from dpsprep.options import parse_all_options
from dpsprep.workdir import WorkingDirectory
from dpsprep.workflow import attempt_to_optimize_result, combine_document, process_in_pool


# OCR options
@click.option('--socr', type=str, default=None, help='"Streamlined" OCR; `--ocrs eng,grc` expands to `--ocr \'{"language": ["eng", "grc"]}\'`.')
@click.option('--ocr', type=str, default=None, help='Perform OCR via OCRmyPDF rather than trying to convert the text layer. If this parameter has a value, it should be a JSON dictionary of options to be passed to OCRmyPDF.')
# Other options
@click.option('-p', '--pool-size', type=click.IntRange(min=0), default=4, help='Size of MultiProcessing pool for handling page-by-page operations.')
@click.option('-O3', 'optlevel', flag_value=3, help='Use the aggressive lossy PDF image optimization from OCRmyPDF.')
@click.option('-O2', 'optlevel', flag_value=2, help='Use the PDF image optimization from OCRmyPDF.')
@click.option('-O1', 'optlevel', flag_value=1, help='Use the lossless PDF image optimization from OCRmyPDF (without performing OCR).')
@click.option('-t', '--no-text', is_flag=True, help='Disable the generation of text layers. Implied by --ocr.')
@click.option('-v', '--verbose', is_flag=True, help='Display debug messages.')
@click.option('-o', 'deprecated_overwrite', is_flag=True, help='Deprecated flag for overwriting destination file. The short variant of --overwrite has been renamed to -f.')
@click.option('-f', '--overwrite', is_flag=True, help='Overwrite destination file.')
@click.option('-w', '--preserve-working', is_flag=True, help='Preserve the working directory after script termination.')
@click.option('-d', '--delete-working', is_flag=True, help='Delete any existing files in the working directory prior to writing to it.')
# Range options
@click.option('-q', '--quality', type=str, default='', help="A range group option that determines the quality of images in output. Valid values range between 1 and 100. Used only for JPEG compression, i.e. RGB and Grayscale images. Passed directly to Pillow and to OCRmyPDF's optimizer.")
@click.option('--dpi', type=str, default='', help='A range group option that allows overriding DPI values encoded in the DjVu file for individual pages.')
@click.option('-m', '--mode', type=str, default='infer', help='A range group option that allows overriding the image modes encoded in the DjVu file for individual pages.  Valid values are `infer` (default), `bitonal`, `grayscale` and `rgb`. It sometimes makes sense to force bitonal images since they compress well.')
@click.version_option()
@click.argument('dest', type=click.Path(exists=False, resolve_path=True), required=False)
@click.argument('src', type=click.Path(exists=True, resolve_path=True), required=True)
@click.command(epilog='See dpsprep(1) for more details.')
def dpsprep(
    # Positional arguments
    src: str,
    dest: str | None,
    # Range options
    mode: str,
    dpi: str,
    quality: str,
    # Other options
    delete_working: bool,
    preserve_working: bool,
    overwrite: bool,
    deprecated_overwrite: bool,
    verbose: bool,
    no_text: bool,
    optlevel: int | None,
    pool_size: int,
    # OCR options
    ocr: str | None,
    socr: str | None,
) -> None:
    """Convert DjVu files to PDF.

    The name comes from Sony's Digital Paper System (DPS), for which the tool was initially developed.

    The usage should be straightforward, however the options that accept page ranges require some
    elaboration. For example, the --mode option accepts the following values:

        `rgb`, `rgb[3]`, `rgb[3-4]`, `rgb[3-end]`, `rgb[3],rgb[10-end]`
    """
    configure_loguru(verbose=verbose)

    if deprecated_overwrite:
        click.echo(
            click.style(
                'Warning: The short variant of --overwrite has been renamed from -o to -f. The -o flag will be removed in the next major release.',
                fg='yellow',
            ),
            err=True,
        )

        overwrite = deprecated_overwrite

    try:
        options = parse_all_options(
            ocr=ocr,
            socr=socr,
            mode=mode,
            dpi=dpi,
            quality=quality,
            no_text=no_text,
            pool_size=pool_size,
            verbose=verbose,
            optlevel=optlevel,
        )
    except DpsPrepConfigError as err:
        raise click.ClickException(str(err)) from err

    workdir = WorkingDirectory(src, dest)

    if not overwrite and workdir.dest.exists():
        raise click.ClickException(f'File {workdir.dest} already exists.')

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
