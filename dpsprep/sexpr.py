from typing import Generic, TypeVar, Union

import djvu.sexpr
import loguru

T = TypeVar('T')
R = TypeVar('R')


class SExpressionVisitor(Generic[R]):
    def visit_list(self, node: djvu.sexpr.ListExpression, **kwargs: T) -> Union[R, None]:
        if len(node) > 0 and isinstance(node[0], djvu.sexpr.SymbolExpression):
            method = getattr(self, f'visit_list_{node[0]}', None)
            if method is None:
                loguru.logger.warning(f"Don't know how to visit ListExpression of type {str(node[0])!r}.")
                return None
            return method(node, **kwargs)
        if hasattr(self, 'visit_plain_list'):
            return self.visit_plain_list(node, **kwargs)
        loguru.logger.warning("Don't know how to visit a plain ListExpression.")
        return None

    def visit_other(self, node: djvu.sexpr.Expression, **kwargs: T) -> Union[R, None]:  # noqa: ARG002
        loguru.logger.warning(f"Don't know how to visit S-expression type {type(node)!r}.")
        return None

    def visit(self, node: djvu.sexpr.Expression, **kwargs: T) -> Union[R, None]:
        if isinstance(node, djvu.sexpr.IntExpression):
            if hasattr(self, 'visit_int'):
                return self.visit_int(node, **kwargs)
            loguru.logger.warning("Don't know how to visit IntExpression.")
            return None
        if isinstance(node, djvu.sexpr.StringExpression):
            if hasattr(self, 'visit_string'):
                return self.visit_string(node, **kwargs)
            loguru.logger.warning("Don't know how to visit StringExpression.")
            return None
        if isinstance(node, djvu.sexpr.ListExpression):
            return self.visit_list(node, **kwargs)
        return self.visit_other(node, **kwargs)
