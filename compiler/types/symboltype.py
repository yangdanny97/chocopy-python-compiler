from typing import Optional


class SymbolType:
    # base class for types

    def isValueType() -> bool:
        return False

    def isListType() -> bool:
        return False

    def isFuncType() -> bool:
        return False

    def elementType():
        return None

    def isSpecialType() -> bool:
        return False

    def toJSON(self, dump_location=True):
        raise Exception("unsupported")
