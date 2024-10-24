import djvu.sexpr
import loguru
from pdfrw import IndirectPdfDict, PdfDict, PdfName

from .sexpr import SExpressionVisitor


# Based on
# https://github.com/pmaupin/pdfrw/issues/52#issuecomment-271190546
class OutlineTransformVisitor(SExpressionVisitor[PdfDict]):
    def visit_plain_list(self, node: djvu.sexpr.StringExpression, parent: IndirectPdfDict) -> PdfDict:
        title, page, *rest = node
        # I have experimentally determined that we need to translate page indices. -- Ianis, 2023-05-03
        try:
            page_number = int(page.value[1:]) - 1
        except ValueError:
            # As far as I understand, python-djvulibre doesn't support Djvu's page titles. -- Ianis, 2023-12-09
            loguru.logger.warning(f'Could not determine page number from the page title {page.value}.')
            return None

        bookmark = IndirectPdfDict(
            Parent = parent,
            Title = title.value,
            A = PdfDict(
                D = [page_number, PdfName.Fit],
                S = PdfName.GoTo,
            ),
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

    def visit_list_bookmarks(self, node: djvu.sexpr.ListExpression) -> PdfDict:
        _, *rest = node

        outline = IndirectPdfDict()

        for child in rest:
            self.visit(child, parent=outline)

        return outline
