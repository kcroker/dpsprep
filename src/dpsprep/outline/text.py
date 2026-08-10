# ruff: file-ignore[no-self-use, unused-unpacked-variable]

import importlib
import logging
import unicodedata
from collections.abc import Iterable
from typing import Protocol

import djvu.decode
import djvu.sexpr
from fpdf import FPDF

from dpsprep.options import DpsPrepOptions

from .sexpr_visitor import SExpressionVisitor


BASE_FONT_SIZE = 10
TAB_SIZE = 4
logger = logging.getLogger(__name__)


class TextExtractVisitor(SExpressionVisitor[str]):
    def iter_chars(self, string: str) -> Iterable[str]:
        for char in string:
            code = unicodedata.category(char)

            # Line Separator (Zl) | Space Separator (Zs)
            if code in {'Zl', 'Zs'}:
                yield ' '

            # Paragraph Separator (Zp)
            elif code == 'Zp':
                yield '\n'

            # Control (Cc)
            elif code == 'Cc':
                if char == '\t':
                    yield ' ' * TAB_SIZE
                elif char == '\n':
                    yield ' '

            # These break FPDF.
            # A full list of categories can be found in https://www.compart.com/en/unicode/category
            # Format (Cf) | Private Use (Co) | Surrogate 'Cs':
            elif code in {'Cf', 'Co', 'Cs'}:
                pass

            else:
                yield char

    def visit_string(self, node: djvu.sexpr.StringExpression) -> str:
        try:
            string = node.value  # This getter is not static - it does UTF-8 conversion and fails for some DjVu files
        except ValueError as err:
            logger.warning(f'Could not decode {node!r}: {err}')
            return ''
        else:
            return ''.join(self.iter_chars(string))

    # ruff: ignore[unused-method-argument]
    def visit_plain_list(self, node: djvu.sexpr.ListExpression) -> str:
        return ''

    def visit_list_word(self, node: djvu.sexpr.ListExpression) -> str | None:
        _, x1, y1, x2, y2, content, *rest = node
        return self.visit(content)

    visit_list_char = visit_list_word

    def visit_list_line(self, node: djvu.sexpr.ListExpression) -> str:
        _, x1, y1, x2, y2, *rest = node
        return ' '.join(self.visit(child) or '' for child in rest)

    def visit_list_para(self, node: djvu.sexpr.ListExpression) -> str:
        _, x1, y1, x2, y2, *rest = node
        return '\n'.join(self.visit(child) or '' for child in rest)

    visit_list_column = visit_list_para
    visit_list_region = visit_list_para
    visit_list_page = visit_list_para


class TextDrawVisitor(SExpressionVisitor):
    pdf: FPDF
    dpi: int
    extractor: TextExtractVisitor

    def __init__(self, pdf: FPDF, dpi: int) -> None:
        self.pdf = pdf
        self.dpi = dpi
        self.extractor = TextExtractVisitor()

    # ruff: ignore[unused-method-argument]
    def draw_text(self, x1: int, x2: int, y1: int, y2: int, text: str) -> None:
        page_width, page_height = self.pdf.pages[self.pdf.page].dimensions()

        if page_height is None:
            logger.warning(f'Cannot draw {text!r} because page height is not set.')
            return

        self.pdf.set_font('Invisible', size=BASE_FONT_SIZE)

        # Adjust font size
        desired_width = (x2 - x1) / self.dpi
        actual_width = self.pdf.get_string_width(text)

        if actual_width == 0:
            return

        self.pdf.set_font('Invisible', size=int(BASE_FONT_SIZE * desired_width / actual_width))

        try:
            self.pdf.text(x=x1 / self.dpi, y=page_height / 72 - y1 / self.dpi, text=text)
        except TypeError as err:
            logger.warning(f'FPDF refuses to draw {text!r}: {err}')

    def iter_loose_string_content(self, expressions: list[djvu.sexpr.Expression]) -> Iterable[str]:
        for child in expressions:
            if not isinstance(child, djvu.sexpr.StringExpression):
                continue

            if (text := self.extractor.visit(child)) is not None:
                yield text

    def get_loose_string_content(self, expressions: list[djvu.sexpr.Expression], delimiter: str) -> str:
        return delimiter.join(self.iter_loose_string_content(expressions))

    def visit_list_word(self, node: djvu.sexpr.ListExpression) -> None:
        _, x1, y1, x2, y2, *rest = node
        text = self.extractor.visit(node)

        if text is not None:
            self.draw_text(x1.value, x2.value, y1.value, y2.value, text)

    visit_list_char = visit_list_word

    def visit_list_line(self, node: djvu.sexpr.ListExpression) -> None:
        _, x1, y1, x2, y2, *rest = node

        text = self.get_loose_string_content(rest, ' ')

        if len(text) > 0:
            self.draw_text(x1.value, x2.value, y1.value, y2.value, text)

        for child in rest:
            if not isinstance(child, djvu.sexpr.StringExpression):
                self.visit(child)

    def visit_list_para(self, node: djvu.sexpr.ListExpression) -> None:
        _, x1, y1, x2, y2, *rest = node

        text = self.get_loose_string_content(rest, '\n')

        if len(text) > 0:
            self.draw_text(x1.value, x2.value, y1.value, y2.value, text)

        for child in rest:
            if not isinstance(child, djvu.sexpr.StringExpression):
                self.visit(child)

    def visit_list_column(self, node: djvu.sexpr.ListExpression) -> None:
        _, x1, y1, x2, y2, *rest = node

        for child in rest:
            self.visit(child)

    visit_list_page = visit_list_column
    visit_list_region = visit_list_column


class TextExtractionTracker(Protocol):
    def mark_page_as_processed(self, i: int) -> None:
        ...

    def mark_all_pages_as_processed(self) -> None:
        ...


def extract_text_as_fpdf(
    document: djvu.decode.Document,
    options: DpsPrepOptions,
    tracker: TextExtractionTracker | None = None,
) -> FPDF:
    pdf = FPDF(unit='in')

    with importlib.resources.path('dpsprep', 'invisible1.ttf') as fspath:
        pdf.add_font(
            family='Invisible',
            fname=fspath.as_posix(),
            style='',
        )

    for i, page in enumerate(document.pages):
        page_job = page.decode(wait=True)
        page_dpi = options.dpi_overrides.get_value_for_zero_based_page(i) or page_job.dpi

        # This annotation will get fixed in the next release after 2.8.7
        #   See https://github.com/py-pdf/fpdf2/commit/9dbd2da8c382f03bac7f23721d6dde9f130dd967
        pdf.add_page(format=(page_job.width / page_dpi, page_job.height / page_dpi))  # type: ignore[arg-type]

        logger.debug(f'Processing text for page {i + 1}.')
        visitor = TextDrawVisitor(pdf, page_dpi)
        visitor.visit(page.text.sexpr)

        if tracker:
            tracker.mark_page_as_processed(i)

    return pdf
