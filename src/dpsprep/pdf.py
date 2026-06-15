import pathlib

import pdfrw

from dpsprep.options import DpsPrepOptions


def is_valid_pdf(path: pathlib.Path) -> bool:
    try:
        pdfrw.PdfReader(path)
    except pdfrw.errors.PdfParseError:
        return False
    else:
        return True


def combine_pdfs_on_fs_with_text(options: DpsPrepOptions, outline: pdfrw.IndirectPdfDict) -> None:
    text_pdf = pdfrw.PdfReader(options.workdir.text_layer_pdf_path)
    writer = pdfrw.PdfWriter()

    for i, text_page in enumerate(text_pdf.pages):
        # We take the one-page text PDF and add the image layer on top
        # Even if the font was not invisible, it would be hidden visually (but not during search or text highlight)
        image_pdf = pdfrw.PdfReader(options.workdir.get_page_pdf_path(i))
        image_page = image_pdf.pages[0]
        merger = pdfrw.PageMerge(text_page)
        merger.add(image_page).render()
        writer.addpage(text_page)

    writer.trailer.Root.Outlines = outline
    writer.write(options.workdir.combined_pdf_path)


def combine_pdfs_on_fs_without_text(options: DpsPrepOptions, outline: pdfrw.IndirectPdfDict, max_page: int) -> None:
    writer = pdfrw.PdfWriter()

    for i in range(max_page):
        image_pdf = pdfrw.PdfReader(options.workdir.get_page_pdf_path(i))
        image_page = image_pdf.pages[0]
        writer.addpage(image_page)

    writer.trailer.Root.Outlines = outline
    writer.write(options.workdir.combined_pdf_without_text_path)
