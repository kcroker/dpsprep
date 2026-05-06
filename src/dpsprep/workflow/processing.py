import multiprocessing
from time import time

import djvu.decode
import loguru

from dpsprep.images import failsafe_save_djvu_page, process_djvu_page
from dpsprep.logging import configure_loguru, human_readable_size
from dpsprep.options import DpsPrepOptions
from dpsprep.outline import extract_text_as_fpdf
from dpsprep.pdf import is_valid_pdf
from dpsprep.workdir import WorkingDirectory


def process_page_bg(workdir: WorkingDirectory, options: DpsPrepOptions, i: int) -> None:
    """Process a page image.

    It is assumed that this will run in a worker, so the document must be read anew and loguru must be (re)configured.
    """
    configure_loguru(verbose=options.verbose)
    page_number = i + 1

    if workdir.get_page_pdf_path(i).exists():
        if is_valid_pdf(workdir.get_page_pdf_path(i)):
            loguru.logger.debug(f'Image data from page {page_number} already processed.')
            return
        loguru.logger.debug(f'Invalid page generated for {page_number}, regenerating.')
    else:
        loguru.logger.debug(f'Processing image data from page {page_number}.')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src),
    )
    document.decoding_job.wait()

    page_bg = process_djvu_page(document.pages[i], options.mode, i)

    failsafe_save_djvu_page(
        page_bg,
        workdir.get_page_pdf_path(i),
        options.quality,
        options.dpi,
        page_number,
    )

    pdf_size = workdir.get_page_pdf_path(i).stat().st_size
    loguru.logger.debug(f'Image data with size {human_readable_size(pdf_size)} from page {page_number} processed in {time() - start_time:.2f}s and written to working directory.')


def process_text(workdir: WorkingDirectory, options: DpsPrepOptions) -> None:
    """Process the text of the entire document.

    It is assumed that this will run in a worker, so the document must be read anew and loguru must be (re)configured.
    """
    configure_loguru(verbose=options.verbose)

    if workdir.text_layer_pdf_path.exists():
        loguru.logger.info('Text data already processed.')
        return

    loguru.logger.debug('Processing text data.')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src),
    )
    document.decoding_job.wait()

    fpdf = extract_text_as_fpdf(document, options.dpi)
    fpdf.output(str(workdir.text_layer_pdf_path))

    pdf_size = workdir.text_layer_pdf_path.stat().st_size
    loguru.logger.info(f'Text data with size {human_readable_size(pdf_size) } processed in {time() - start_time:.2f}s and written to working directory')


def process_in_pool(workdir: WorkingDirectory, options: DpsPrepOptions, document: djvu.decode.Document) -> None:
    djvu_size = workdir.src.stat().st_size
    loguru.logger.info(f'Processing {workdir.src} with {len(document.pages)} pages and size {human_readable_size(djvu_size)} using {options.pool_size} workers.')

    pool = multiprocessing.Pool(processes=options.pool_size)
    tasks = list[multiprocessing.pool.AsyncResult]()

    if not options.no_text:
        tasks.append(pool.apply_async(func=process_text, args=[workdir, options]))

    for i in range(len(document.pages)):
        tasks.append(pool.apply_async(func=process_page_bg, args=[workdir, options, i]))

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
    loguru.logger.info('Processed all pages.')
