from .symboltype import SymbolType


class ValueType(SymbolType):
    def isValueType():
        return True

    def isNone(self):
        return False

    def toJSON(self, dump_location=True):
        raise Exception("unsupported")

    def getJavaSignature(self) -> str:
        raise Exception("unsupported")

    def isJavaRef(self) -> bool:
        raise Exception("unsupported")

    def isListType(self):
        raise Exception("unsupported")
