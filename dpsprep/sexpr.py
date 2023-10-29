from loguru import logger
import djvu.sexpr


class SExpressionVisitor:
    def visit_list(self, node: djvu.sexpr.ListExpression, **kwargs):
        if len(node) > 0 and isinstance(node[0], djvu.sexpr.SymbolExpression):
            method = getattr(self, f'visit_list_{node[0]}', None)
            if method is None:
                logger.warning(f"Don't know how to visit ListExpression of type {repr(str(node[0]))}.")
            else:
                return method(node, **kwargs)
        else:
            if hasattr(self, 'visit_plain_list'):
                return self.visit_plain_list(node, **kwargs)
            else:
                logger.warning("Don't know how to visit a plain ListExpression.")

    def visit_other(self, node: djvu.sexpr.Expression, **kwargs):
        logger.warning(f"Don't know how to visit S-expression type {repr(type(node))}.")

    def visit(self, node: djvu.sexpr.Expression, **kwargs):
        if isinstance(node, djvu.sexpr.IntExpression):
            if hasattr(self, 'visit_int'):
                return self.visit_int(node, **kwargs)
            else:
                logger.warning("Don't know how to visit IntExpression.")
        elif isinstance(node, djvu.sexpr.StringExpression):
            if hasattr(self, 'visit_string'):
                return self.visit_string(node, **kwargs)
            else:
                logger.warning("Don't know how to visit StringExpression.")
        elif isinstance(node, djvu.sexpr.ListExpression):
            return self.visit_list(node, **kwargs)
        else:
            return self.visit_other(node, **kwargs)
