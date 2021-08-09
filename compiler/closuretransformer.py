from .typechecker import TypeChecker
from .typesystem import TypeSystem
from collections import defaultdict
from .astnodes import *
from .types import *

class ClosureTransformer(TypeChecker):
    # rewriting function signatures to include free vars as explicit arguments
    # rewrite function calls to include new args

    def __init__(self):
        super().__init__(TypeSystem())
        self.addErrors = False

    def typeToAnnotation(self, t: ValueType)->SymbolType:
        if isinstance(t, ListValueType):
            return ListType([0,0], self.typeToAnnotation(t.elementType))
        elif isinstance(t, ClassValueType):
            return ClassType([0,0], t.className)

    def FuncDef(self, node: FuncDef):
        for fv in node.freevars:
            ident = Identifier(node.location, fv.name)
            annot = self.typeToAnnotation(fv.inferredType)
            tv = TypedVar(node.location, ident, annot)
            tv.t = fv.inferredType
            tv.t.isRef = True
            node.params.append(tv)
        return super().FuncDef(node)

    def getSignature(self, node: FuncDef):
        rType = self.visit(node.returnType)
        t = FuncType([self.visit(t) for t in node.params], rType)
        t.freevars = node.freevars
        return t

    def callHelper(self, node):
        t = None
        if isinstance(node, CallExpr):
            fname = node.function.name
            if self.ts.classExists(fname):
                t = self.ts.getMethod(fname, "__init__")
            else:
                t = self.getType(fname)
        if isinstance(node, MethodCallExpr):
            class_name, member_name = node.method.object.inferredType.className, node.method.member.name
            t = self.ts.getMethod(class_name, member_name)
        if t is None or len(t.freevars) == 0 or not isinstance(t, FuncType):
            return
        for fv in t.freevars:
            ident = Identifier(node.location, fv.name)
            ident.inferredType = fv.inferredType
            node.args.append(ident)

    def CallExpr(self, node: CallExpr):
        self.callHelper(node)
        return super().CallExpr(node)

    def MethodCallExpr(self, node: MethodCallExpr):
        self.callHelper(node)
        return super().MethodCallExpr(node)

    # add ref type annotations
    def TypedVar(self, node: TypedVar):
        # return the type of the annotaton
        node.t = self.visit(node.type)
        if node.capturedNonlocal:
            node.t.isRef = True
        return node.t
        

