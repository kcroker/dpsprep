from djvu import sexpr
from pdfrw import IndirectPdfDict

from .outline import OutlineTransformVisitor


def test_basic_outline() -> None:
    src = sexpr.ListExpression([
        sexpr.SymbolExpression(sexpr.Symbol('bookmarks')),
        sexpr.ListExpression([
            sexpr.StringExpression(b'Chapter 2'),
            sexpr.StringExpression(b'#100'),
        ]),
    ])

    visitor = OutlineTransformVisitor()
    bookmarks = visitor.visit(src)
    assert bookmarks is not None
    assert bookmarks.Count == 1
    assert bookmarks.First.Title == 'Chapter 2'
    assert bookmarks.First.A.D[0] == 99  # The page number


def test_nested_outline() -> None:
    src = sexpr.ListExpression([
        sexpr.SymbolExpression(sexpr.Symbol('bookmarks')),
        sexpr.ListExpression([
            sexpr.StringExpression(b'Chapter 2'),
            sexpr.StringExpression(b'#100'),
            sexpr.ListExpression([
                sexpr.StringExpression(b'Chapter 2.1'),
                sexpr.StringExpression(b'#200'),
            ]),
        ]),
    ])

    visitor = OutlineTransformVisitor()
    bookmarks = visitor.visit(src)
    assert bookmarks is not None
    assert bookmarks.Count == 1
    assert bookmarks.First.Count == 1
    assert bookmarks.First.A.D[0] == 99  # The page number of chapter 2
    assert bookmarks.First.First.A.D[0] == 199  # The page number of chapter 2.1


# Sometimes the page numbers are instead page titles, which our libdjvu bindings do not support
# We ignore them since there is not much we can do in this case
# See https://github.com/kcroker/dpsprep/issues/23
def test_outline_with_page_titles() -> None:
    src = sexpr.ListExpression([
        sexpr.SymbolExpression(sexpr.Symbol('bookmarks')),
        sexpr.ListExpression([
            sexpr.StringExpression(b'Preface'),
            sexpr.StringExpression(b'#f007.djvu'),
        ]),
        sexpr.ListExpression([
            sexpr.StringExpression(b'Contents'),
            sexpr.StringExpression(b'#f011.djvu'),
        ]),
        sexpr.ListExpression([
            sexpr.StringExpression(b'0 Prologue'),
            sexpr.StringExpression(b'#p001.djvu'),
        ]),
    ])

    visitor = OutlineTransformVisitor()
    bookmarks = visitor.visit(src)
    empty_pdf_dict = IndirectPdfDict()
    assert bookmarks == empty_pdf_dict
