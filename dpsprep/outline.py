from loguru import logger
from pdfrw import PdfName, PdfDict, IndirectPdfDict
import djvu.sexpr
import re

from .sexpr import SExpressionVisitor


# Based on
# https://github.com/pmaupin/pdfrw/issues/52#issuecomment-271190546
class OutlineTransformVisitor(SExpressionVisitor):
    def __init__(self, toc_pg_offset: int, total_pages: int):
        self.toc_pg_offset = toc_pg_offset
        self.total_pages = total_pages
        super().__init__()
    def visit_plain_list(self, node: djvu.sexpr.StringExpression, parent: IndirectPdfDict):
        title, page, *rest = node

        # Translate the first valid number in the page title to be the page indices.
        m = re.search(r'[0-9]+', page.value)
        if m is not None:
            page_number = int(m.group(0), base=10) + self.toc_pg_offset
        else:
            logger.warning(f'Could not determine page number from the page title {page.value}.')
            return

        if page_number < 0 or page_number >= self.total_pages:
            logger.warning(f'Refuse to translate the page title \'{page.value}\' to an invalid number {page_number}.')
            return

        bookmark = IndirectPdfDict(
            Parent = parent,
            Title = title.value,
            A = PdfDict(
                D = [page_number, PdfName.Fit],
                S = PdfName.GoTo
            )
        )

        if parent.Count is None:
            parent.Count = 0
            parent.First = bookmark
        else:
            bookmark.Prev = parent.Last
            bookmark.Prev.Next = bookmark

        parent.Count += 1
        parent.Last = bookmark

        for child in rest:
            self.visit(child, parent=bookmark)

        return bookmark

    def visit_list_bookmarks(self, node: djvu.sexpr.ListExpression):
        _, *rest = node

        outline = IndirectPdfDict()

        for child in rest:
            self.visit(child, parent=outline)

        return outline
