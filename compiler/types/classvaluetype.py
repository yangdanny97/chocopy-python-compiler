from .valuetype import ValueType
from llvmlite import ir


class SpecialClass:
    BOOL = 'bool'
    STR = 'str'
    INT = 'int'
    NONE = '<None>'
    EMPTY = '<Empty>'
    OBJECT = 'object'


class ClassValueType(ValueType):
    def __init__(self, className: str):
        self.className = className

    def __eq__(self, other):
        if isinstance(other, ClassValueType):
            return self.className == other.className
        return False

    def isListType(self) -> bool:
        return self.className in {SpecialClass.EMPTY, SpecialClass.NONE}

    def getJavaSignature(self, isList=False) -> str:
        if self.className == SpecialClass.BOOL:
            if isList:
                return "Ljava/lang/Boolean;"
            else:
                return "Z"
        elif self.className == SpecialClass.STR:
            return "Ljava/lang/String;"
        elif self.className == SpecialClass.OBJECT:
            return "Ljava/lang/Object;"
        elif self.className == SpecialClass.INT:
            if isList:
                return "Ljava/lang/Integer;"
            else:
                return "I"
        elif self.className == SpecialClass.NONE:
            return "Ljava/lang/Object;"
        elif self.className == SpecialClass.EMPTY:
            return "[Ljava/lang/Object;"
        else:
            return "L" + self.className + ";"

    def isNone(self) -> bool:
        return self.className == SpecialClass.NONE

    def isSpecialType(self) -> bool:
        return self.className in [SpecialClass.INT, SpecialClass.STR, SpecialClass.BOOL]

    def isJavaRef(self) -> bool:
        return self.className not in [SpecialClass.INT, SpecialClass.BOOL]

    def getJavaName(self, isList=False) -> str:
        if self.className == SpecialClass.BOOL:
            if isList:
                return "java/lang/Boolean"
            else:
                return "boolean"
        elif self.className == SpecialClass.STR:
            return "java/lang/String"
        elif self.className == SpecialClass.OBJECT:
            return "java/lang/Object"
        elif self.className == SpecialClass.NONE:
            return "java/lang/Object"
        elif self.className == SpecialClass.EMPTY:
            return "[Ljava/lang/Object;"
        elif self.className == SpecialClass.INT:
            if isList:
                return "java/lang/Integer"
            else:
                return self.className
        else:
            return self.className

    def getCILSignature(self) -> str:
        if self.className == SpecialClass.NONE:
            return "void"
        else:
            return self.getCILName()

    def getCILName(self) -> str:
        if self.className == SpecialClass.BOOL:
            return "bool"
        elif self.className == SpecialClass.STR:
            return "string"
        elif self.className == SpecialClass.OBJECT:
            return "object"
        elif self.className == SpecialClass.NONE:
            return "object"
        elif self.className == SpecialClass.EMPTY:
            return "object[]"
        elif self.className == SpecialClass.INT:
            return "int64"
        else:
            return "class " + self.className

    def getWasmName(self) -> str:
        # bools are i32, ints are i64
        # all others are pointers/refs, which are i32
        if self.className == SpecialClass.BOOL:
            return "i32"
        elif self.className == SpecialClass.STR:
            return "i32"
        elif self.className == SpecialClass.OBJECT:
            return "i32"
        elif self.className == SpecialClass.NONE:
            return "i32"
        elif self.className == SpecialClass.EMPTY:
            return "i32"
        elif self.className == SpecialClass.INT:
            return "i64"
        else:
            return "i32"

    def __str__(self):
        return self.className

    def __hash__(self):
        return str(self).__hash__()

    def toJSON(self, dump_location=True) -> dict:
        return {
            "kind": "ClassValueType",
            "className": self.className
        }

    def getLLVMType(self) -> ir.Type:
        if self.className == SpecialClass.BOOL:
            return ir.IntType(1)
        elif self.className == SpecialClass.STR:
            return ir.IntType(8).as_pointer()
        elif self.className == SpecialClass.OBJECT:
            return ir.IntType(8).as_pointer()
        elif self.className == SpecialClass.NONE:
            return ir.IntType(8).as_pointer()
        elif self.className == SpecialClass.EMPTY:
            return ir.IntType(8).as_pointer()
        elif self.className == SpecialClass.INT:
            return ir.IntType(32)
        else:
            return ir.IntType(8).as_pointer()
