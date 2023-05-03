from pdfrw import PdfName, PdfDict, IndirectPdfDict
import djvu.sexpr

from .sexpr import SExpressionVisitor


# Based on
# https://github.com/pmaupin/pdfrw/issues/52#issuecomment-271190546
class OutlineTransformVisitor(SExpressionVisitor):
    def visit_plain_list(self, node: djvu.sexpr.StringExpression, parent: IndirectPdfDict):
        title, page, *rest = node
        # I have experimentally determined that we need to translate page indices. -- Ianis, 2023-05-03
        page_number = int(page.value[1:]) - 1

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
