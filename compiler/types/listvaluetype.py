from .valuetype import ValueType


class ListValueType(ValueType):

    def __init__(self, elementType: ValueType):
        self.elementType = elementType

    def __eq__(self, other):
        if isinstance(other, ListValueType):
            return self.elementType == other.elementType
        return False

    def getJavaSignature(self, _=False):
        return "["+self.elementType.getJavaSignature(True)

    def getJavaName(self, _=False):
        return "["+self.elementType.getJavaSignature(True)

    def getCILName(self, _=False):
        return self.elementType.getCILName() + "[]"

    def getCILSignature(self, _=False):
        return self.getCILName()

    def isListType(self):
        return True

    def isJavaRef(self):
        return True

    def __str__(self):
        return "[{}]".format(str(self.elementType))

    def __hash__(self):
        return str(self).__hash__()

    def toJSON(self, dump_location=True):
        return {
            "kind": "ListValueType",
            "elementType": self.elementType.toJSON(dump_location)
        }
