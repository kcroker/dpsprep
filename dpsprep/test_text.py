import string

import djvu.decode
import pytest

from .text import TextExtractVisitor


def remove_whitespace(src: str) -> str:
    return src.translate({ord(c): None for c in string.whitespace})


def test_extract_djvu_page_text_words() -> None:
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu'),
    )
    document.decoding_job.wait()

    djvu_page = document.pages[0]
    djvu_page.get_info()
    djvu_text = TextExtractVisitor().visit(djvu_page.text.sexpr)

    assert djvu_text is not None

    with open('fixtures/lipsum_01.txt') as file:
        source_pdf_text = file.read()

    assert remove_whitespace(djvu_text) == remove_whitespace(source_pdf_text)


def test_extract_djvu_page_text_lines() -> None:
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_lines.djvu'),
    )
    document.decoding_job.wait()

    djvu_page = document.pages[0]
    djvu_page.get_info()
    djvu_text = TextExtractVisitor().visit(djvu_page.text.sexpr)

    assert djvu_text is not None

    with open('fixtures/lipsum_01.txt') as file:
        source_pdf_text = file.read()

    assert remove_whitespace(djvu_text) == remove_whitespace(source_pdf_text)


def test_invalid_utf8() -> None:
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words_invalid.djvu'),
    )
    document.decoding_job.wait()

    djvu_page = document.pages[0]
    djvu_page.get_info()
    first_word_sexpr = djvu_page.text.sexpr[5][5]

    # djvulibre cannot decode the first word
    with pytest.raises(UnicodeDecodeError):
        first_word_sexpr.value  # noqa: B018

    first_word = TextExtractVisitor().visit(first_word_sexpr)
    assert first_word == ''
