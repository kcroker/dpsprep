from loguru import logger
from pypdf import PdfWriter
from pypdf.generic._base import IndirectObject
import djvu.sexpr

from .sexpr import SExpressionVisitor


class OutlineTransformVisitor(SExpressionVisitor):
    output: PdfWriter

    def __init__(self, output: PdfWriter):
        self.output = output

    def visit_plain_list(self, node: djvu.sexpr.StringExpression, parent: IndirectObject):
        title, page, *rest = node

        result = self.output.add_outline_item(
            title=title.value,
            page_number=int(page.value[1:]),
            parent=parent
        )

        for child in rest:
            self.visit(child, parent=result)

        return result

    def visit_list_bookmarks(self, node: djvu.sexpr.ListExpression):
        _, *rest = node

        for child in rest:
            self.visit(child, parent=None)
