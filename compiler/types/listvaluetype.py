from .valuetype import ValueType
import llvmlite

class ListValueType(ValueType):
    
    def __init__(self, elementType:ValueType):
        self.elementType = elementType

    def __eq__(self, other):
        if isinstance(other, ListValueType):
            return self.elementType == other.elementType
        return False

    def isListType():
        return True

    def __str__(self):
        return "[{}]".format(str(self.elementType))

    def __hash__(self):
        return str(self).__hash__()

    def toJSON(self):
        return {
            "kind": "ListValueType",
            "elementType": self.elementType.toJSON()
        }