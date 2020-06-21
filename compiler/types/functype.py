from .valuetype import ValueType
from .symboltype import SymbolType

class FuncType(SymbolType):
    def __init__(self, parameters:[ValueType], returnType:ValueType):
        self.parameters = parameters
        self.returnType = returnType
        self.freevars = [] # used in AST transformations, not printed out

    def __eq__(self, other):
        if isinstance(other, FuncType):
            return self.parameters == other.parameters and self.returnType == other.returnType
        return False

    def methodEquals(self, other):
        if isinstance(other, FuncType) and len(self.parameters) > 0 and len(other.parameters) > 0:
            return self.parameters[1:] == other.parameters[1:] and self.returnType == other.returnType
        return False

    def isFuncType():
        return True

    def __str__(self):
        paramStr = ",".join([str(t) for t in self.parameters])
        return F"[{paramStr}]->{self.returnType}"
    
    def __hash__(self):
        paramStr = ",".join([str(t) for t in self.parameters])
        return (F"[{paramStr}]->{self.returnType}").__hash__()

    def toJSON(self):
        return {
            "kind": "FuncType",
            "parameters": [p.toJSON() for p in self.parameters],
            "returnType": self.returnType.toJSON()
        }