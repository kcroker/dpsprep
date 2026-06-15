import logging
import multiprocessing
from time import time

import djvu.decode

from dpsprep.images import failsafe_save_djvu_page, process_djvu_page
from dpsprep.logging import configure_logging, human_readable_size
from dpsprep.options import DEFAULT_IMAGE_MODE, DpsPrepOptions
from dpsprep.outline import extract_text_as_fpdf
from dpsprep.pdf import is_valid_pdf


logger = logging.getLogger(__name__)


def process_page_bg(options: DpsPrepOptions, i: int) -> None:
    """Process a page image.

    It is assumed that this will run in a worker, so the document must be read anew and logging must be (re)configured.
    """
    configure_logging(verbose=options.verbose)
    page_number = i + 1

    if options.workdir.get_page_pdf_path(i).exists():
        if is_valid_pdf(options.workdir.get_page_pdf_path(i)):
            logger.debug(f'Image data from page {page_number} already processed.')
            return
        logger.debug(f'Invalid page generated for {page_number}, regenerating.')
    else:
        logger.debug(f'Processing image data from page {page_number}.')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(options.workdir.src),
    )
    document.decoding_job.wait()

    mode = options.mode_overrides.get_value_for_zero_based_page(i) or DEFAULT_IMAGE_MODE
    page_bg = process_djvu_page(document.pages[i], mode, i)
    failsafe_save_djvu_page(
        page_bg,
        options.workdir.get_page_pdf_path(i),
        options,
        page_number,
    )

    dpi_override = options.dpi_overrides.get_value_for_zero_based_page(i)
    pdf_size = options.workdir.get_page_pdf_path(i).stat().st_size

    message = (
        f'Processed and saved image data for page {page_number} in {time() - start_time:.2f}s. '
        f'The result has {page_bg.mode} mode, DPI {page_bg.resolution} '
        + ('' if dpi_override is None else f'(will be rescaled to {dpi_override}) ') +
        f'and size {human_readable_size(pdf_size)}.'
    )

    logger.debug(message)


def process_text(options: DpsPrepOptions) -> None:
    """Process the text of the entire document.

    It is assumed that this will run in a worker, so the document must be read anew and logging must be (re)configured.
    """
    configure_logging(verbose=options.verbose)

    if options.workdir.text_layer_pdf_path.exists():
        logger.info('Text data already processed.')
        return

    logger.debug('Processing text data.')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(options.workdir.src),
    )
    document.decoding_job.wait()

    fpdf = extract_text_as_fpdf(document, options)
    fpdf.output(str(options.workdir.text_layer_pdf_path))

    pdf_size = options.workdir.text_layer_pdf_path.stat().st_size
    logger.info(f'Text data with size {human_readable_size(pdf_size) } processed in {time() - start_time:.2f}s and written to working directory')


def process_in_pool(options: DpsPrepOptions, document: djvu.decode.Document) -> None:
    djvu_size = options.workdir.src.stat().st_size
    logger.info(f'Processing {options.workdir.src} with {len(document.pages)} pages and size {human_readable_size(djvu_size)} using {options.pool_size} workers.')

    pool = multiprocessing.Pool(processes=options.pool_size)
    tasks = list[multiprocessing.pool.AsyncResult]()

    if not options.no_text:
        tasks.append(pool.apply_async(func=process_text, args=[options]))

    for i in range(len(document.pages)):
        tasks.append(pool.apply_async(func=process_page_bg, args=[options, i]))

    pool.close()
    pool_is_working = True

    while pool_is_working:
        pool_is_working = False

        for task in tasks:
            try:
                task.get(timeout=25)
            except multiprocessing.TimeoutError:
                pool_is_working = True

    pool.join()
    logger.info('Processed all pages.')
