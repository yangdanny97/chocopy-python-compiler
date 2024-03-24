from .valuetype import ValueType
from llvmlite import ir


class ListValueType(ValueType):
    elementType: ValueType

    def __init__(self, elementType: ValueType):
        self.elementType = elementType

    def __eq__(self, other):
        if isinstance(other, ListValueType):
            return self.elementType == other.elementType
        return False

    def getJavaSignature(self, isList=False) -> str:
        return "[" + self.elementType.getJavaSignature(True)

    def getJavaName(self, isList=False) -> str:
        return "[" + self.elementType.getJavaSignature(True)

    def getCILName(self) -> str:
        return self.elementType.getCILName() + "[]"

    def getCILSignature(self) -> str:
        return self.getCILName()

    def isListType(self) -> bool:
        return True

    def isJavaRef(self) -> bool:
        return True

    def __str__(self):
        return "[{}]".format(str(self.elementType))

    def __hash__(self):
        return str(self).__hash__()

    def toJSON(self, dump_location=True) -> dict:
        return {
            "kind": "ListValueType",
            "elementType": self.elementType.toJSON(dump_location)
        }

    def getWasmName(self) -> str:
        return "i32"

    def getLLVMType(self) -> ir.Type:
        return ir.IntType(8).as_pointer()
