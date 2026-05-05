import shutil

import djvu.decode
import loguru
import pdfrw

from dpsprep.ocrmypdf_adapter import perform_ocr
from dpsprep.options import DpsPrepOptions
from dpsprep.outline import extract_outline_as_pdfdict
from dpsprep.pdf import combine_pdfs_on_fs_with_text, combine_pdfs_on_fs_without_text
from dpsprep.workdir import WorkingDirectory


def combine_document(workdir: WorkingDirectory, options: DpsPrepOptions, document: djvu.decode.Document) -> None:
    outline = pdfrw.IndirectPdfDict()

    if len(document.outline.sexpr) > 0:
        loguru.logger.info('Processing metadata.')
        outline = extract_outline_as_pdfdict(document)
        loguru.logger.info('Metadata processed.')
    else:
        loguru.logger.info('No metadata to process.')

    loguru.logger.info('Combining everything.')

    if options.no_text:
        combine_pdfs_on_fs_without_text(workdir, outline, len(document.pages))

        ocr_success = False

        if options.ocr_options:
            loguru.logger.info('Performing OCR.')
            ocr_success = perform_ocr(workdir, options.ocr_options)
        else:
            loguru.logger.info('Skipping the text layer.')

        if not ocr_success:
            shutil.copy(workdir.combined_pdf_without_text_path, workdir.combined_pdf_path)
    else:
        combine_pdfs_on_fs_with_text(workdir, outline)
