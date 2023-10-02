import pdfrw

from .workdir import WorkingDirectory


def combine_pdfs_on_fs(workdir: WorkingDirectory, outline: pdfrw.IndirectPdfDict):
    text_pdf = pdfrw.PdfReader(workdir.text_pdf_path)
    writer = pdfrw.PdfWriter()

    for i, page in enumerate(text_pdf.pages):
        merger = pdfrw.PageMerge(page)
        image_pdf = pdfrw.PdfReader(workdir.get_page_pdf_path(i))
        merger.add(image_pdf.pages[0]).render()
        writer.addpage(page)

    writer.trailer.Root.Outlines = outline
    writer.write(workdir.combined_pdf_path)
