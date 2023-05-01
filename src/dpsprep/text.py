from reportlab.pdfgen.canvas import Canvas
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
    canvas: Canvas
    extractor: TextExtractVisitor

    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.extractor = TextExtractVisitor()

    def visit_drawable_list(self, node: djvu.sexpr.ListExpression, text: str):
        _, x1, y1, x2, y2, *rest = node

        # Based on
        # https://github.com/ocropus/hocr-tools/blob/v1.3.0/hocr-pdf
        tobject = self.canvas.beginText()
        tobject.setTextRenderMode(3) # 3 = Invisible
        tobject.setTextOrigin(x1.value, y1.value)

        # Adjust font size
        desired_width = x2.value - x1.value
        actual_width = self.canvas.stringWidth(text, 'Invisible', BASE_FONT_SIZE)

        if actual_width == 0:
            return

        tobject.setFont('Invisible', BASE_FONT_SIZE * desired_width / actual_width)

        # Draw text
        tobject.textLine(text)
        self.canvas.drawText(tobject)

    def visit_list_word(self, node: djvu.sexpr.ListExpression):
        self.visit_drawable_list(node, self.extractor.visit(node))

    def visit_list_line(self, node: djvu.sexpr.ListExpression):
        self.visit_drawable_list(node, self.extractor.visit(node))

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
