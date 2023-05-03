import multiprocessing
import os
import shutil
from time import time

import click
import djvu.decode
import pdfrw
from loguru import logger
from PIL import Image

from .images import ImageMode, djvu_page_to_image
from .logging import configure_loguru, human_readable_size
from .outline import OutlineTransformVisitor
from .pdf import combine_pdfs_on_fs, substitute_outline
from .text import djvu_pages_to_text_fpdf
from .workdir import WorkingDirectory


def process_page_bg(workdir: WorkingDirectory, mode: ImageMode, quality: int, i: int):
    page_number = i + 1

    if workdir.get_page_pdf_path(i).exists():
        logger.info(f'Image data from page {page_number} already processed')
        return
    else:
        logger.debug(f'Processing image data from page {page_number}')

    start_time = time()
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src)
    )
    document.decoding_job.wait()

    image_pdf_raw = djvu_page_to_image(document.pages[i], mode)
    image_pdf_raw.save(
        workdir.get_page_pdf_path(i),
        format='PDF',
        quality=quality
    )

    pdf_size = os.path.getsize(workdir.get_page_pdf_path(i))
    logger.info(f'Image data with size {human_readable_size(pdf_size)} from page {page_number} processed in {time() - start_time:.2f}s and written to working directory')


def process_text(workdir: WorkingDirectory):
    if workdir.text_pdf_path.exists():
        logger.info('Text data already processed')
        return
    else:
        logger.debug('Processing text data')

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
@click.option('-p', '--pool-size', type=click.IntRange(min=0), default=4, help='Size of MultiProcessing pool for handling page-by-page operations.')
@click.option('-q', '--quality', type=click.IntRange(min=0, max=100), default=75, help="Quality of images in output. Used only for JPEG compression, i.e. RGB and Grayscale images. Passed directly to Pillow.")
@click.option('-m', '--mode', type=click.Choice(['bitonal', 'grayscale', 'rgb']), default='bitonal', help='Image mode.')
@click.argument('dest', type=click.Path(exists=False, resolve_path=True), required=False)
@click.argument('src', type=click.Path(exists=True, resolve_path=True), required=True)
@click.command()
def dpsprep(
    src: str,
    dest: str | None,
    mode: ImageMode,
    quality: int,
    pool_size: int,
    verbose: bool,
    overwrite: bool,
    delete_working: bool,
    preserve_working: bool
):
    configure_loguru(verbose)
    workdir = WorkingDirectory(src, dest)

    if not overwrite and workdir.dest.exists():
        logger.error(f'File {workdir.dest} already exists.')
        return

    if mode == 'bitonal':
        if not hasattr(Image.core, 'libtiff_encoder'):  # type: ignore
            logger.warning('Bitonal image compression may suffer because Pillow has been built without libtiff support.')
    else:
        if not hasattr(Image.core, 'libjpeg_encoder'):  # type: ignore
            logger.warning('Multitonal image compression may suffer because Pillow has been built without libjpeg support.')

    if delete_working:
        if workdir.working.exists():
            logger.info(f'Removing existing working directory {workdir.working}.')
            shutil.rmtree(workdir.working)
        else:
            logger.info(f'Working directory {workdir.working} does not exist.')
    else:
        if workdir.working.exists():
            logger.info(f'Working directory {workdir.working} already exists.')
        else:
            logger.info(f'Working directory {workdir.working} does not exist and will be created.')

    workdir.create_if_necessary()

    logger.info(f'Processing {workdir.src} with {pool_size} workers.')
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI(workdir.src)
    )
    document.decoding_job.wait()

    pool = multiprocessing.Pool(processes=pool_size)
    tasks: list[multiprocessing.AsyncResult] = []
    tasks.append(pool.apply_async(func=process_text, args=[workdir]))

    for i in range(len(document.pages)):
        # Cannot pass the page object itself because it does not support serialization for IPC
        tasks.append(pool.apply_async(func=process_page_bg, args=[workdir, mode, quality, i]))

    pool.close()

    for task in tasks:
        try:
            task.get(timeout=100)
        except multiprocessing.TimeoutError:
            pass

    pool.join()

    logger.info('Combining image and text data')
    combine_pdfs_on_fs(workdir)

    combined_pdf = pdfrw.PdfReader(workdir.combined_pdf_path)
    outline = pdfrw.IndirectPdfDict()

    if len(document.outline.sexpr) > 0:
        logger.info('Processing metadata')
        outline = OutlineTransformVisitor().visit(document.outline.sexpr)
    else:
        logger.info('No metadata to process')

    final_pdf = substitute_outline(combined_pdf, outline)
    final_pdf.write(workdir.dest)

    dest_size = os.path.getsize(workdir.dest)
    logger.info(f'Output ({human_readable_size(dest_size)}) written to {workdir.dest}')

    if preserve_working:
        logger.info(f'Working directory {workdir.working} will be preserved.')
    else:
        logger.info(f'Deleting the working directory {workdir.working}.')
        shutil.rmtree(workdir.working)