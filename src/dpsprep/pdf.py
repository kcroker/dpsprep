import pdfrw

from .workdir import WorkingDirectory


def combine_pdfs_on_fs(workdir: WorkingDirectory):
    text_pdf = pdfrw.PdfReader(workdir.text_pdf_path)

    for i, page in enumerate(text_pdf.pages):
        merger = pdfrw.PageMerge(page)
        image_pdf = pdfrw.PdfReader(workdir.get_page_pdf_path(i))
        merger.add(image_pdf.pages[0]).render()

    writer = pdfrw.PdfWriter()
    writer.write(workdir.combined_pdf_path, text_pdf)


def substitute_outline(src: pdfrw.PdfReader, outline: pdfrw.IndirectPdfDict):
    writer = pdfrw.PdfWriter()

    for page in src.pages:
        writer.addpage(page)

    writer.trailer.Root.Outlines = outline
    return writer
