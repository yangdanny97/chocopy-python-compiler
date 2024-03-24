from .typechecker import TypeChecker
from .typesystem import TypeSystem
from .astnodes import *
from .types import *


def typeToAnnotation(t: ValueType) -> TypeAnnotation:
    if isinstance(t, ListValueType):
        return ListType([0, 0], typeToAnnotation(t.elementType))
    elif isinstance(t, ClassValueType):
        return ClassType([0, 0], t.className)
    else:
        raise Exception("unexpected type")


class ClosureTransformer(TypeChecker):
    # rewrite function signatures to include free vars as explicit arguments
    # rewrite function calls to include new args

    def __init__(self):
        super().__init__(TypeSystem())
        self.addErrors = False

    def getSignature(self, node: FuncDef):
        rType = self.visit(node.returnType)
        t = FuncType([self.visit(t) for t in node.params], rType)
        t.freevars = node.freevars
        t.refParams = {}

        for i in range(len(node.params)):
            if node.params[i].varInstanceX().isNonlocal:
                t.refParams[i] = node.params[i].varInstanceX()
        for i in range(len(node.freevars)):
            if node.freevars[i].varInstanceX().isNonlocal:
                t.refParams[len(node.params) +
                            i] = node.freevars[i].varInstanceX()
        return t

    def funcParams(self, node: FuncDef):
        for fv in node.freevars:
            ident = fv.copy()
            assert isinstance(ident.inferredType, ValueType)
            annot = typeToAnnotation(ident.inferredType)
            tv = TypedVar(node.location, ident, annot)
            tv.varInstance = ident.varInstance
            tv.t = ident.inferredType
            node.params.append(tv)

    def callHelper(self, node):
        t = None
        if isinstance(node, CallExpr):
            fname = node.function.name
            if self.ts.classExists(fname):
                t = self.ts.getMethod(fname, "__init__")
            else:
                t = self.getType(fname)
        if isinstance(node, MethodCallExpr):
            assert isinstance(node.method.object.inferredType, ClassValueType)
            class_name, member_name = node.method.object.inferredType.className, node.method.member.name
            t = self.ts.getMethod(class_name, member_name)
        if t is None or len(t.freevars) == 0 or not isinstance(t, FuncType):
            return
        for fv in t.freevars:
            node.args.append(fv.copy())

    def CallExpr(self, node: CallExpr):
        self.callHelper(node)
        return super().CallExpr(node)

    def MethodCallExpr(self, node: MethodCallExpr):
        self.callHelper(node)
        return super().MethodCallExpr(node)
