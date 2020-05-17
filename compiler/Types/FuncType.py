from .ValueType import ValueType
from .SymbolType import SymbolType

class FuncType(SymbolType):
    def __init__(self, parameters:[ValueType], returnType:ValueType):
        self.parameters = parameters
        self.returnType = returnType

    def __eq__(self, other):
        if isinstance(other, FuncType):
            return self.parameters == other.parameters and self.returnType == other.returnType
        return False

    def isFuncType():
        return True