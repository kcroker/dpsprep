import functools
import logging
import operator
from time import time

import click
import djvu.decode

from dpsprep.concurrency import concurrently_process_document
from dpsprep.exceptions import DpsPrepConcurrencyError
from dpsprep.logging import configure_logging, human_readable_size
from dpsprep.options import (
    DpiOverridesClickType,
    DpsPrepOptions,
    ImageMode,
    ImageModeOverridesClickType,
    JsonObject,
    OcrOptionClickType,
    QualityOverridesClickType,
    SocrOptionClickType,
    get_default_pool_size,
)
from dpsprep.range import RangeOptionGroup
from dpsprep.workflow import (
    attempt_to_optimize_result,
    combine_document,
    destroy_workdir,
    initialize_workdir,
)


logger = logging.getLogger(__name__)


# OCR options
@click.option('--socr', 'socr_options', type=SocrOptionClickType(), default=None, help='"Streamlined" OCR; `--ocrs eng,grc` expands to `--ocr \'{"language": ["eng", "grc"]}\'`.')
@click.option('--ocr', 'ocr_options', type=OcrOptionClickType(), default=None, help='Perform OCR via OCRmyPDF rather than trying to convert the text layer. If this parameter has a value, it should be a JSON dictionary of options to be passed to OCRmyPDF.')
# Other options
@click.option('-p', '--pool-size', type=click.IntRange(min=1), default=None, help='Size of the MultiProcessing pool that handles page-by-page operations. Defaults to os.process_cpu_count() with a fallback to 2 * os.cpu_count()')
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
@click.option('-q', '--quality', 'quality_overrides', type=QualityOverridesClickType(), multiple=True, default=[], help="Determine the quality of images in output. Valid values range between 1 and 100. Used only for JPEG compression, i.e. RGB and Grayscale images. Passed directly to Pillow and to OCRmyPDF's optimizer.")
@click.option('--dpi', 'dpi_overrides', type=DpiOverridesClickType(), multiple=True, default=[], help='Override the DPI values encoded in the DjVu file for individual pages.')
@click.option('-m', '--mode', 'mode_overrides', type=ImageModeOverridesClickType(), multiple=True, default=['infer'], help='Override the image modes encoded in the DjVu file for individual pages. Valid values are "infer" (default), "bitonal", "grayscale" and "rgb". It sometimes makes sense to force bitonal images since they compress well.')
@click.version_option()
@click.argument('dest', type=click.Path(exists=False, resolve_path=True), required=False)
@click.argument('src', type=click.Path(exists=True, resolve_path=True), required=True)
@click.command(epilog='See dpsprep(1) for more details.')
@click.pass_context
def dpsprep(
    ctx: click.Context,
    # Positional arguments
    src: str,
    dest: str | None,
    # Range options
    mode_overrides: tuple[RangeOptionGroup[ImageMode], ...],
    dpi_overrides: tuple[RangeOptionGroup[int], ...],
    quality_overrides: tuple[RangeOptionGroup[int], ...],
    # Other options
    delete_working: bool,
    preserve_working: bool,
    overwrite: bool,
    deprecated_overwrite: bool,
    verbose: bool,
    no_text: bool,
    optlevel: int | None,
    pool_size: int | None,
    # OCR options
    ocr_options: JsonObject | None,
    socr_options: JsonObject | None,
) -> None:
    """Convert DjVu files to PDF.

    The name comes from Sony's Digital Paper System (DPS), for which the tool was initially developed.

    The usage should be straightforward, however the options that accept page ranges require some
    elaboration. For example, the --mode option accepts the following values:

        "rgb", "rgb[3]", "rgb[3,4,5]", "rgb[3-5]", "rgb[3-end]", "bitonal[3],rgb[10-end]"

    Furthermore, --mode can be passed multiple times with the same effect as placing commas.
    """
    configure_logging(verbose=verbose)

    if deprecated_overwrite:
        click.echo(
            click.style(
                'Warning: The short variant of --overwrite has been renamed from -o to -f. The -o flag will be removed in the next major release.',
                fg='yellow',
            ),
            err=True,
        )

        overwrite = deprecated_overwrite

    if ocr_options and socr_options:
        raise click.ClickException('Cannot specify both --ocr and -socr simultaneously.')

    workdir = initialize_workdir(src, dest, delete_working)

    if not overwrite and workdir.dest.exists():
        raise click.ClickException(f'File {workdir.dest} already exists.')

    options = DpsPrepOptions(
        workdir=workdir,
        mode_overrides=functools.reduce(operator.or_, mode_overrides),
        dpi_overrides=functools.reduce(operator.or_, dpi_overrides, RangeOptionGroup([])),
        quality_overrides=functools.reduce(operator.or_, quality_overrides, RangeOptionGroup([])),
        no_text=no_text or bool(ocr_options or socr_options),
        ocr_options=ocr_options or socr_options,
        optlevel=optlevel,
        pool_size=pool_size or get_default_pool_size(),
        verbose=verbose,
    )

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src),
    )
    document.decoding_job.wait()
    djvu_size = workdir.src.stat().st_size

    try:
        concurrently_process_document(options, document)
    except DpsPrepConcurrencyError:
        # We assume that the actual error has been logged, so we ignore its message.
        ctx.abort()

    combine_document(options, document)

    combined_size = workdir.combined_pdf_path.stat().st_size
    logger.info(f'Produced a combined output file with size {human_readable_size(combined_size)} in {time() - start_time:.2f}s. This is {round(100 * combined_size / djvu_size, 2)}% of the DjVu source file.')

    attempt_to_optimize_result(options, djvu_size, combined_size)

    if preserve_working:
        logger.info(f'Working directory {workdir.working} will be preserved.')
    else:
        logger.info(f'Deleting the working directory {workdir.working}.')
        destroy_workdir(workdir)
