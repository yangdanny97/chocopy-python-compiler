from .symboltype import SymbolType
import llvmlite.ir as ir


class ValueType(SymbolType):
    def isValueType() -> bool:
        return True

    def isNone(self) -> bool:
        return False

    def toJSON(self, dump_location=True):
        raise Exception("unsupported")

    def getJavaSignature(self) -> str:
        raise Exception("unsupported")

    def isJavaRef(self) -> bool:
        raise Exception("unsupported")

    def isListType(self) -> bool:
        raise Exception("unsupported")

    def getLLVMType(self) -> ir.Type:
        raise Exception("unsupported")

    def getWasmName(self) -> str:
        raise Exception("unsupported")
