from pathlib import Path
from typing import Sequence

from loguru import logger
from fpdf import FPDF
import djvu.sexpr

from .sexpr import SExpressionVisitor


BASE_FONT_SIZE = 10


class TextExtractVisitor(SExpressionVisitor):
    def visit_string(self, node: djvu.sexpr.StringExpression):
        return node.value

    def visit_plain_list(self, node: djvu.sexpr.ListExpression):
        return ''

    def visit_list_word(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, content, *rest = node
        return self.visit(content)

    def visit_list_line(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node
        return ' '.join(self.visit(child) or '' for child in rest)

    def visit_list_para(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node
        return '\n'.join(self.visit(child) or '' for child in rest)

    def visit_list_column(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node
        return '\n'.join(self.visit(child) or '' for child in rest)

    def visit_list_page(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node
        return '\n'.join(self.visit(child) or '' for child in rest)


class TextDrawVisitor(SExpressionVisitor):
    pdf: FPDF
    extractor: TextExtractVisitor

    def __init__(self, pdf: FPDF):
        self.pdf = pdf
        self.extractor = TextExtractVisitor()

    def visit_list_word(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node
        text = self.extractor.visit(node)

        self.pdf.set_font('Invisible', size=BASE_FONT_SIZE)
        self.pdf.get_string_width(text)

        # Adjust font size
        desired_width = x2.value - x1.value
        actual_width = self.pdf.get_string_width(text)

        self.pdf.set_font('Invisible', size=BASE_FONT_SIZE * desired_width / actual_width)

        page_width, page_height = self.pdf.pages[self.pdf.page].dimensions()
        self.pdf.text(x=x1.value, y=page_height - y1.value, txt=text)

    def visit_list_line(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node

        for child in rest:
            self.visit(child)

    def visit_list_para(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node

        for child in rest:
            self.visit(child)

    def visit_list_column(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node

        for child in rest:
            self.visit(child)

    def visit_list_page(self, node: djvu.sexpr.ListExpression):
        _, x1, y1, x2, y2, *rest = node

        for child in rest:
            self.visit(child)


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
        fname=Path(__file__).parent.parent.parent / 'invisible1.ttf',
        style=''
    )

    for i, page in enumerate(pages):
        page_job = page.decode(wait=True)
        pdf.add_page(format=page_job.size)
        logger.debug(f'Processing text for page {i + 1}')
        visitor = TextDrawVisitor(pdf)
        visitor.visit(page.text.sexpr)

    return pdf
