from .astnodes import *
from .types import *
from .visitor import Visitor

# A utility visitor to erase the inferred types of expressions
class TypeEraser(Visitor):

    def visit(self, node: Node):
        if isinstance(node, Expr):
            node.inferredType = None
        return node.visitChildren(self)


