import pathlib

import pdfrw

from .workdir import WorkingDirectory


def is_valid_pdf(path: pathlib.Path) -> bool:
    try:
        pdfrw.PdfReader(path)
    except pdfrw.errors.PdfParseError:
        return False
    else:
        return True


def combine_pdfs_on_fs_with_text(workdir: WorkingDirectory, outline: pdfrw.IndirectPdfDict) -> None:
    text_pdf = pdfrw.PdfReader(workdir.text_layer_pdf_path)
    writer = pdfrw.PdfWriter()

    for i, page in enumerate(text_pdf.pages):
        merger = pdfrw.PageMerge(page)
        image_pdf = pdfrw.PdfReader(workdir.get_page_pdf_path(i))
        merger.add(image_pdf.pages[0]).render()
        writer.addpage(page)

    writer.trailer.Root.Outlines = outline
    writer.write(workdir.combined_pdf_path)


def combine_pdfs_on_fs_without_text(workdir: WorkingDirectory, outline: pdfrw.IndirectPdfDict, max_page: int) -> None:
    writer = pdfrw.PdfWriter()

    for i in range(max_page):
        image_pdf = pdfrw.PdfReader(workdir.get_page_pdf_path(i))
        writer.addpage(image_pdf.pages[0])

    writer.trailer.Root.Outlines = outline
    writer.write(workdir.combined_pdf_without_text_path)
