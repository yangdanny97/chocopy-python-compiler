from .ValueType import ValueType

class ListValueType(ValueType):
        def __init__(self, elementType:ValueType):
        self.elementType = elementType

    def __eq__(self, other):
        if isinstance(other, ListType):
            return self.elementType == other.elementType
        return False

    def isListType():
        return True