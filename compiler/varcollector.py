from typing import Sequence, List
from .astnodes import *
from .types import *
from .visitor import Visitor


class VarCollector(Visitor):
    # simple visitor to collect all the identifiers used as expressions or assignment targets
    vars: List[Identifier]

    def __init__(self):
        self.vars = []

    def getVars(self, node: Node):
        self.visit(node)
        return self.vars

    def getVarsFromList(self, nodes: Sequence[Node]):
        for n in nodes:
            self.visit(n)
        return self.vars

    def visit(self, node: Node):
        return node.postorder(self)

    def Identifier(self, node: Identifier):
        self.vars.append(node)
