from .declaration import Declaration
from .identifier import Identifier
from .vardef import VarDef
from .funcdef import FuncDef
from .typedvar import TypedVar
from .classtype import ClassType
from ..types.classvaluetype import ClassValueType
from ..types.functype import FuncType
from ..types.Types import NoneType
from typing import List


class ClassDef(Declaration):

    def __init__(self, location: List[int], name: Identifier, superclass: Identifier, declarations: List[Declaration]):
        super().__init__(location, "ClassDef")
        self.name = name
        self.superclass = superclass
        for d in declarations:
            if isinstance(d, VarDef):
                d.isAttr = True
                d.attrOfClass = name.name
            if isinstance(d, FuncDef):
                d.isMethod = True
        self.declarations = declarations

    def preorder(self, visitor):
        visitor.ClassDef(self)
        for d in self.declarations:
            visitor.visit(d)
        return self

    def postorder(self, visitor):
        for d in self.declarations:
            visitor.visit(d)
        return visitor.ClassDef(self)

    def visit(self, visitor):
        return visitor.ClassDef(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name.toJSON(dump_location)
        d["superClass"] = self.superclass.toJSON(dump_location)
        d["declarations"] = [decl.toJSON(dump_location)
                             for decl in self.declarations]
        return d

    def getIdentifier(self) -> Identifier:
        return self.name

    def getDefaultConstructor(self) -> FuncDef:
        var_decls: List[Declaration] = [
            d for d in self.declarations if isinstance(d, VarDef)]
        constructor = FuncDef(self.location,
                              Identifier(self.location, "__init__"),
                              [TypedVar(self.location,
                                        Identifier(self.location, "self"),
                                        ClassType(self.location,
                                                  self.name.name)
                                        )],
                              ClassType(self.location, "<None>"),
                              var_decls,
                              [], True
                              )
        constructor.params[0].t = ClassValueType(self.name.name)
        constructor.type = FuncType(
            [ClassValueType(self.name.name)], NoneType())
        return constructor
