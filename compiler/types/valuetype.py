from .symboltype import SymbolType

class ValueType(SymbolType):
    def isValueType():
        return True

    def toJSON(self, dump_location=True):
        raise Exception("unsupported")