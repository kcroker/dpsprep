import string

import djvu.decode

from .text import TextExtractVisitor


def remove_whitespace(src: str):
    return src.translate({ord(c): None for c in string.whitespace})


def test_extract_djvu_page_text_words():
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu')
    )
    document.decoding_job.wait()

    djvu_page = document.pages[0]
    djvu_page.get_info()
    djvu_text = TextExtractVisitor().visit(djvu_page.text.sexpr)

    with open('fixtures/lipsum_01.txt') as file:
        source_pdf_text = file.read()

    assert remove_whitespace(djvu_text) == remove_whitespace(source_pdf_text)


def test_extract_djvu_page_text_lines():
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_lines.djvu')
    )
    document.decoding_job.wait()

    djvu_page = document.pages[0]
    djvu_page.get_info()
    djvu_text = TextExtractVisitor().visit(djvu_page.text.sexpr)

    with open('fixtures/lipsum_01.txt') as file:
        source_pdf_text = file.read()

    assert remove_whitespace(djvu_text) == remove_whitespace(source_pdf_text)
