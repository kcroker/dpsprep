import djvu.decode
from pypdf import PdfReader

from .text import TextExtractVisitor


def test_extract_djvu_page_text_words():
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu')
    )
    document.decoding_job.wait()

    visitor = TextExtractVisitor()
    djvu_page = document.pages[0]
    djvu_page.get_info()
    djvu_text = visitor.visit(djvu_page.text.sexpr)

    source_pdf = PdfReader('fixtures/lipsum.pdf')
    source_pdf_text = source_pdf.pages[0].extract_text()

    assert djvu_text == source_pdf_text


def test_extract_djvu_page_text_lines():
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_lines.djvu')
    )
    document.decoding_job.wait()

    visitor = TextExtractVisitor()
    djvu_page = document.pages[0]
    djvu_page.get_info()
    djvu_text = visitor.visit(djvu_page.text.sexpr)

    source_pdf = PdfReader('fixtures/lipsum.pdf')
    source_pdf_text = source_pdf.pages[0].extract_text()

    assert djvu_text == source_pdf_text
