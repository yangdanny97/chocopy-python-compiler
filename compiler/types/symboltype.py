from typing import Optional, Self


class SymbolType:
    # base class for types

    def isValueType(self) -> bool:
        return False

    def isListType(self) -> bool:
        return False

    def isFuncType(self) -> bool:
        return False

    def isSpecialType(self) -> bool:
        return False

    def toJSON(self, dump_location=True) -> dict:
        raise Exception("unsupported")
