from .valuetype import ValueType
from .symboltype import SymbolType

class FuncType(SymbolType):
    def __init__(self, parameters:[ValueType], returnType:ValueType):
        self.parameters = parameters
        self.returnType = returnType

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