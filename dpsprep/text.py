import unicodedata
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Union

import djvu.sexpr
import loguru
from fpdf import FPDF

from .sexpr import SExpressionVisitor

BASE_FONT_SIZE = 10
TAB_SIZE = 4


class TextExtractVisitor(SExpressionVisitor[str]):
    def iter_chars(self, string: str) -> Iterable[str]:
        for char in string:
            code = unicodedata.category(char)

            # Line Separator (Zl) | Space Separator (Zs)
            if code in ('Zl', 'Zs'):
                yield ' '

            # Paragraph Separator (Zp)
            elif code == 'Zp':
                yield '\n'

            # Control (Cc)  # noqa: ERA001
            elif code == 'Cc':
                if char == '\t':
                    yield ' ' * TAB_SIZE
                elif char == '\n':
                    yield ' '

            # These break FPDF.
            # A full list of categories can be found in https://www.compart.com/en/unicode/category
            # Format (Cf) | Private Use (Co) | Surrogate 'Cs':
            elif code in ('Cf', 'Co', 'Cs'):
                pass

            else:
                yield char

    def visit_string(self, node: djvu.sexpr.StringExpression) -> str:
        try:
            string = node.value  # This getter is not static - it does UTF-8 conversion and fails for some DjVu files
        except ValueError as err:
            loguru.logger.warning(f'Could not decode {node!r}: {err}')
            return ''
        else:
            return ''.join(self.iter_chars(string))

    def visit_plain_list(self, node: djvu.sexpr.ListExpression) -> str:  # noqa: ARG002
        return ''

    def visit_list_word(self, node: djvu.sexpr.ListExpression) -> Union[str, None]:
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
    extractor: TextExtractVisitor

    def __init__(self, pdf: FPDF) -> None:
        self.pdf = pdf
        self.extractor = TextExtractVisitor()

    def draw_text(self, x1: int, x2: int, y1: int, y2: int, text: str) -> None:  # noqa: ARG002
        page_width, page_height = self.pdf.pages[self.pdf.page].dimensions()

        if page_height is None:
            loguru.logger.warning(f'Cannot draw {text!r} because page height is not set.')
            return

        self.pdf.set_font('Invisible', size=BASE_FONT_SIZE)
        self.pdf.get_string_width(text)

        # Adjust font size
        desired_width = x2 - x1
        actual_width = self.pdf.get_string_width(text)

        if actual_width == 0:
            return

        self.pdf.set_font('Invisible', size=int(BASE_FONT_SIZE * desired_width / actual_width))

        try:
            self.pdf.text(x=x1, y=page_height - y1, text=text)
        except TypeError as err:
            loguru.logger.warning(f'FPDF refuses to draw {text!r}: {err}')

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


# We do not need any visible fonts. Actually we could use some of the default PDF type 1 fonts,
# but then non-latin script would get all messed up. Using a true-type font, even one that doesn't
# support esoteric characters, would still let us encode the text correctly.
# The font embedded here is taken from https://www.angelfire.com/pr/pgpf/if.html.
# It is small (12kb) and contains (invisible) Latin, Cyrillic and Greek characters.
# After encoding Chinese characters, however, Evince still handles them correctly.
def djvu_pages_to_text_fpdf(pages: Sequence[djvu.decode.Page]) -> FPDF:
    pdf = FPDF(unit='pt')
    pdf.add_font(
        family='Invisible',
        fname=Path(__file__).parent / 'invisible1.ttf',
        style='',
    )

    for i, page in enumerate(pages):
        page_job = page.decode(wait=True)
        pdf.add_page(format=page_job.size)
        loguru.logger.debug(f'Processing text for page {i + 1}.')
        visitor = TextDrawVisitor(pdf)
        visitor.visit(page.text.sexpr)

    return pdf
