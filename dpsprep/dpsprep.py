from time import time
from typing import Union
import json
import multiprocessing.pool
import os.path
import shutil

import click
import djvu.decode
import pdfrw
from loguru import logger

from .images import djvu_page_to_image
from .logging import configure_loguru, human_readable_size
from .ocrmypdf import optimize_pdf, perform_ocr
from .outline import OutlineTransformVisitor
from .pdf import combine_pdfs_on_fs_with_text, combine_pdfs_on_fs_without_text, is_valid_pdf
from .text import djvu_pages_to_text_fpdf
from .workdir import WorkingDirectory


def process_page_bg(workdir: WorkingDirectory, quality: int, i: int):
    page_number = i + 1

    if workdir.get_page_pdf_path(i).exists():
        if is_valid_pdf(workdir.get_page_pdf_path(i)):
            logger.debug(f'Image data from page {page_number} already processed.')
            return
        else:
            logger.debug(f'Invalid page generated for {page_number}, regenerating.')
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
    logger.debug(f'Image data with size {human_readable_size(pdf_size)} from page {page_number} processed in {time() - start_time:.2f}s and written to working directory.')


def process_text(workdir: WorkingDirectory):
    if workdir.text_layer_pdf_path.exists():
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
    fpdf.output(workdir.text_layer_pdf_path)

    pdf_size = os.path.getsize(workdir.text_layer_pdf_path)
    logger.info(f'Text data with size {human_readable_size(pdf_size) } processed in {time() - start_time:.2f}s and written to working directory')


@click.option('-d', '--delete-working', is_flag=True, help='Delete any existing files in the working directory prior to writing to it.')
@click.option('-w', '--preserve-working', is_flag=True, help='Preserve the working directory after script termination.')
@click.option('-o', '--overwrite', is_flag=True, help='Overwrite destination file.')
@click.option('-v', '--verbose', is_flag=True, help='Display debug messages.')
@click.option('-t', '--no-text', is_flag=True, help='Disable the generation of text layers. Implied by --ocr.')
@click.option('-O1', 'optlevel', flag_value=1, help='Use the lossless PDF image optimization from OCRmyPDF (without performing OCR).')
@click.option('-O2', 'optlevel', flag_value=2, help='Use the PDF image optimization from OCRmyPDF.')
@click.option('-O3', 'optlevel', flag_value=3, help='Use the aggressive lossy PDF image optimization from OCRmyPDF.')
@click.option('-p', '--pool-size', type=click.IntRange(min=0), default=4, help='Size of MultiProcessing pool for handling page-by-page operations.')
@click.option('-q', '--quality', type=click.IntRange(min=0, max=100), default=75, help="Quality of images in output. Used only for JPEG compression, i.e. RGB and Grayscale images. Passed directly to Pillow and to OCRmyPDF's optimizer.")
@click.option('--ocr', type=str, is_flag=False, flag_value='{}', help='Perform OCR via OCRmyPDF rather than trying to convert the text layer. If this parameter has a value, it should be a JSON dictionary of options to be passed to OCRmyPDF.')
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
    no_text: bool,
    optlevel: Union[int, None],
    ocr: Union[str, None],
):
    configure_loguru(verbose)
    workdir = WorkingDirectory(src, dest)

    if ocr is None:
        ocr_options = None
    else:
        try:
            ocr_options = json.loads(ocr)
        except ValueError:
            raise SystemExit(f'The OCR options {repr(ocr)} are not valid JSON.')
        else:
            if not isinstance(ocr_options, dict):
                raise SystemExit(f'The OCR options {repr(ocr)} are not a JSON dictionary.')

        no_text = True

    if not overwrite and workdir.dest.exists():
        raise SystemExit(f'File {workdir.dest} already exists.')

    start_time = time()

    if workdir.workdir.exists():
        if delete_working:
            logger.debug(f'Removing existing working directory {workdir.workdir}.')
            workdir.destroy()
            logger.info(f'Removed existing working directory {workdir.workdir}.')
        else:
            logger.info(f'Reusing working directory {workdir.workdir}.')
    else:
        logger.info(f'Working directory {workdir.workdir} has been created.')

    workdir.create_if_necessary()

    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src)
    )
    document.decoding_job.wait()

    djvu_size = os.path.getsize(workdir.src)
    logger.info(f'Processing {workdir.src} with {len(document.pages)} pages and size {human_readable_size(djvu_size)} using {pool_size} workers.')

    pool = multiprocessing.Pool(processes=pool_size)
    tasks: list[multiprocessing.pool.AsyncResult] = []

    if not no_text:
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
    logger.info('Processed all pages.')

    outline = pdfrw.IndirectPdfDict()

    if len(document.outline.sexpr) > 0:
        logger.info('Processing metadata.')
        outline = OutlineTransformVisitor().visit(document.outline.sexpr)
        logger.info('Metadata processed.')
    else:
        logger.info('No metadata to process.')

    logger.info('Combining everything.')

    if no_text:
        combine_pdfs_on_fs_without_text(workdir, outline, len(document.pages))

        if ocr_options is None:
            logger.info('Skipping the text layer.')
            shutil.copy(workdir.combined_pdf_without_text_path, workdir.combined_pdf_path)
        else:
            logger.info('Performing OCR.')
            perform_ocr(workdir, ocr_options)
    else:
        combine_pdfs_on_fs_with_text(workdir, outline)

    combined_size = os.path.getsize(workdir.combined_pdf_path)
    logger.info(f'Produced a combined output file with size {human_readable_size(combined_size)} in {time() - start_time:.2f}s. This is {round(100 * combined_size / djvu_size, 2)}% of the DjVu source file.')

    opt_success = False

    if optlevel is not None:
        logger.info(f'Performing level {optlevel} optimization.')
        opt_success = optimize_pdf(workdir, optlevel, quality, pool_size)

    if opt_success:
        opt_size = os.path.getsize(workdir.optimized_pdf_path)

        logger.info(f'The optimized file has size {human_readable_size(opt_size)}, which is {round(100 * opt_size / combined_size, 2)}% of the raw combined file and {round(100 * opt_size / djvu_size, 2)}% of the DjVu source file.')

        if opt_size < combined_size:
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
