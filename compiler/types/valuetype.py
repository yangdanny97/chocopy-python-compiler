from .symboltype import SymbolType

class ValueType(SymbolType):
    def isValueType():
        return True

    def toJSON(self):
        raise Exception("unsupported")