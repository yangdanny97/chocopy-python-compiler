from .astnodes import *
from .types import *
from .visitor import Visitor
from .varcollector import VarCollector
from typing import List, Dict


def newInstance(tv: TypedVar) -> VarInstance:
    tv.varInstance = VarInstance()
    return tv.varInstance


def merge(d1: dict, d2: dict) -> dict:
    combined = {}
    for k in d1:
        combined[k] = d1[k]
    for k in d2:
        combined[k] = d2[k]
    return combined


def deduplicate(ids: List[Identifier]) -> List[Identifier]:
    seen = set()
    res = []
    for i in ids:
        if i.name in seen:
            continue
        seen.add(i.name)
        res.append(i)
    return res


class ClosureVisitor(Visitor):
    # each variable/parameter declaration has an "instance"
    # each variable is matched to the instance of their declaration

    # instances that are captured by nested functions are marked as refs
    # instances that correspond to global variables are marked as such
    globals: Dict[str, VarInstance]
    decls: List[Dict[str, VarInstance]]

    def __init__(self):
        self.globals = {}
        self.decls = []

    def getInstance(self, name: str) -> VarInstance:
        for i in self.decls[::-1]:
            if name in i:
                return i[name]
        return self.globals[name]

    def visit(self, node: Node):
        if isinstance(node, Expr) or isinstance(node, Stmt):
            return node.postorder(self)
        return node.visit(self)

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, VarDef):
                self.globals[d.getIdentifier().name] = newInstance(d.var)
                assert d.var.varInstance is not None
                d.var.varInstance.isGlobal = True
        # mark all top-level vars to be global
        vars = VarCollector().getVarsFromList(node.statements)
        for v in vars:
            v.varInstance = self.globals[v.name]
            v.varInstance.isGlobal = True
        # traverse other decls
        for d in node.declarations:
            if not isinstance(d, VarDef):
                self.visit(d)

    def ClassDef(self, node: ClassDef):
        for d in node.declarations:
            self.visit(d)

    def FuncDef(self, node: FuncDef):
        decls = {}

        handleSelf = True
        for p in node.params:
            decls[p.identifier.name] = newInstance(p)
            if node.isMethod and handleSelf:
                decls[p.identifier.name].isSelf = True
                handleSelf = False
        for d in node.declarations:
            if isinstance(d, GlobalDecl):
                decls[d.variable.name] = self.globals[d.variable.name]
            elif isinstance(d, NonLocalDecl):
                varInstance = self.getInstance(d.variable.name)
                if varInstance.isSelf:
                    raise Exception(
                        "Special parameter 'self' may not be used in a nonlocal declaration")
                varInstance.isNonlocal = True
            elif isinstance(d, VarDef):
                decls[d.getIdentifier().name] = newInstance(d.var)

        self.decls.append(decls)
        vars = VarCollector().getVarsFromList(node.statements)
        freevars = []
        for v in vars:
            v.varInstance = self.getInstance(v.name)
            if v.name not in decls and not v.varInstance.isGlobal:
                freevars.append(v)

        for d in node.declarations:
            if isinstance(d, FuncDef):
                self.visit(d)
                for v in d.freevars:
                    v.varInstance = self.getInstance(v.name)
                    if v.name not in decls and not v.varInstance.isGlobal:
                        freevars.append(v)
        node.freevars = deduplicate(freevars)
        # remove nonlocal decls
        node.declarations = [
            d for d in node.declarations
            if not isinstance(d, NonLocalDecl)
        ]
