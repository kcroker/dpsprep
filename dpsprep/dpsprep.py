from time import time
from typing import List, Union
import multiprocessing.pool
import os.path
import shutil

import click
import djvu.decode
import pdfrw
from loguru import logger

from .images import djvu_page_to_image
from .logging import configure_loguru, human_readable_size
from .optimize import optimize_pdf
from .outline import OutlineTransformVisitor
from .pdf import combine_pdfs_on_fs
from .text import djvu_pages_to_text_fpdf
from .workdir import WorkingDirectory


def process_page_bg(workdir: WorkingDirectory, quality: int, i: int):
    page_number = i + 1

    if workdir.get_page_pdf_path(i).exists():
        logger.info(f'Image data from page {page_number} already processed.')
        return
    else:
        logger.debug(f'Processing image data from page {page_number}.')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src)
    )
    document.decoding_job.wait()

    image_pdf_raw = djvu_page_to_image(document.pages[i], i)
    image_pdf_raw.save(
        workdir.get_page_pdf_path(i),
        format='PDF',
        quality=quality
    )

    pdf_size = os.path.getsize(workdir.get_page_pdf_path(i))
    logger.info(f'Image data with size {human_readable_size(pdf_size)} from page {page_number} processed in {time() - start_time:.2f}s and written to working directory.')


def process_text(workdir: WorkingDirectory):
    if workdir.text_pdf_path.exists():
        logger.info('Text data already processed.')
        return
    else:
        logger.debug('Processing text data.')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src)
    )
    document.decoding_job.wait()

    fpdf = djvu_pages_to_text_fpdf(document.pages)
    fpdf.output(workdir.text_pdf_path)

    pdf_size = os.path.getsize(workdir.text_pdf_path)
    logger.info(f'Text data with size {human_readable_size(pdf_size) } processed in {time() - start_time:.2f}s and written to working directory')


@click.option('-d', '--delete-working', is_flag=True, help='Delete any existing files in the working directory prior to writing to it.')
@click.option('-w', '--preserve-working', is_flag=True, help='Preserve the working directory after script termination.')
@click.option('-o', '--overwrite', is_flag=True, help='Overwrite destination file.')
@click.option('-v', '--verbose', is_flag=True, help='Display debug messages.')
@click.option('-O1', 'optlevel', flag_value=1, help='Use the lossless PDF image optimization from OCRmyPDF (without performing OCR).')
@click.option('-O2', 'optlevel', flag_value=3, help='Use the PDF image optimization from OCRmyPDF.')
@click.option('-O3', 'optlevel', flag_value=3, help='Use the aggressive lossy PDF image optimization from OCRmyPDF.')
@click.option('-p', '--pool-size', type=click.IntRange(min=0), default=4, help='Size of MultiProcessing pool for handling page-by-page operations.')
@click.option('-q', '--quality', type=click.IntRange(min=0, max=100), default=75, help="Quality of images in output. Used only for JPEG compression, i.e. RGB and Grayscale images. Passed directly to Pillow and to OCRmyPDF's optimizer.")
@click.argument('dest', type=click.Path(exists=False, resolve_path=True), required=False)
@click.argument('src', type=click.Path(exists=True, resolve_path=True), required=True)
@click.command()
def dpsprep(
    src: str,
    dest: Union[str, None],
    quality: int,
    pool_size: int,
    verbose: bool,
    overwrite: bool,
    delete_working: bool,
    preserve_working: bool,
    optlevel: Union[int, None],
):
    configure_loguru(verbose)
    workdir = WorkingDirectory(src, dest)

    if not overwrite and workdir.dest.exists():
        logger.error(f'File {workdir.dest} already exists.')
        return

    start_time = time()

    if workdir.workdir.exists():
        if delete_working:
            logger.debug(f'Removing existing working directory {workdir.workdir}.')
            workdir.destroy()
            logger.info(f'Removed existing working directory {workdir.workdir}.')
        else:
            logger.info(f'Working directory {workdir.workdir} does not exist.')
    else:
        logger.info(f'Working directory {workdir.workdir} has been created.')

    workdir.create_if_necessary()
    logger.info(f'Processing {workdir.src} with {pool_size} workers.')
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src)
    )
    document.decoding_job.wait()

    pool = multiprocessing.Pool(processes=pool_size)
    tasks: List[multiprocessing.pool.AsyncResult] = []
    tasks.append(pool.apply_async(func=process_text, args=[workdir]))

    for i in range(len(document.pages)):
        # Cannot pass the page object itself because it does not support serialization for IPC
        tasks.append(pool.apply_async(func=process_page_bg, args=[workdir, quality, i]))

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

    outline = pdfrw.IndirectPdfDict()

    if len(document.outline.sexpr) > 0:
        logger.debug('Processing metadata.')
        outline = OutlineTransformVisitor().visit(document.outline.sexpr)
        logger.info('Metadata processed.')
    else:
        logger.info('No metadata to process.')

    logger.debug('Combining everything')
    combine_pdfs_on_fs(workdir, outline)
    combined_size = os.path.getsize(workdir.combined_pdf_path)
    logger.info(f'Produced a combined output file with size {human_readable_size(combined_size)} in {time() - start_time:.2f}s.')

    opt_success = False

    if optlevel is not None:
        logger.debug(f'Performing level {optlevel} optimization.')
        opt_success = optimize_pdf(workdir, optlevel, quality, pool_size)

    if opt_success:
        raw_size = os.path.getsize(workdir.combined_pdf_path)
        opt_size = os.path.getsize(workdir.optimized_pdf_path)

        logger.info(f'The optimized file has size {human_readable_size(opt_size)}, which is {round(100 * opt_size / raw_size, 2)}% of the raw combined file.')

        if opt_size < raw_size:
            logger.info('Using the optimized file.')
            shutil.copy(workdir.optimized_pdf_path, workdir.dest)
        else:
            logger.info('Using the raw combined file.')
            shutil.copy(workdir.combined_pdf_path, workdir.dest)
    else:
        shutil.copy(workdir.combined_pdf_path, workdir.dest)

    if preserve_working:
        logger.info(f'Working directory {workdir.workdir} will be preserved.')
    else:
        logger.info(f'Deleting the working directory {workdir.workdir}.')
        workdir.destroy()
