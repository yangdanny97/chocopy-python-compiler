from .typechecker import TypeChecker
from .typesystem import TypeSystem
from collections import defaultdict
from .astnodes import *
from .types import *

class ClosureTransformer(TypeChecker):
    # remove all nonlocal & global declarations, rewriting function signatures to 
    # include them as explicit arguments, rewrite callsites to include new args

    def __init__(self):
        super().__init__(TypeSystem())
        self.addErrors = False

    def typeToAnnotation(self, t: ValueType):
        if isinstance(t, ListValueType):
            return ListType([0,0], self.typeToAnnotation(t.elementType))
        elif isinstance(t, ClassValueType):
            return ClassType([0,0], t.className)

    def FuncDef(self, node: FuncDef):
        for n in node.freevars:
            ident = Identifier(node.location, n)
            annot = self.typeToAnnotation(self.visit(ident))
            node.params.append(TypedVar(node.location, ident, annot))
        node.declarations = [d for d in node.declarations if not isinstance(d, NonLocalDecl) and not isinstance(d, GlobalDecl)]
        return super().FuncDef(node)

    def getSignature(self, node: FuncDef):
        rType = self.visit(node.returnType)
        t = FuncType([self.visit(t) for t in node.params], rType)
        t.freevars = node.freevars
        return t

    def callHelper(self, node):
        target = None
        if isinstance(node, CallExpr):
            target = node.function
        if isinstance(node, MethodCallExpr):
            target = node.method
        t = target.inferredType
        if len(t.freevars) == 0 or not isinstance(t, FuncType):
            return
        for n in t.freevars:
            ident = Identifier(node.location, n)
            self.visit(ident)
            node.args.append(ident)

    def CallExpr(self, node: CallExpr):
        self.callHelper(node)
        return super().CallExpr(node)

    def MethodCallExpr(self, node: MethodCallExpr):
        self.callHelper(node)
        return super().MethodCallExpr(node)
        

