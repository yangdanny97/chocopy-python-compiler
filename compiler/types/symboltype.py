class SymbolType:
    # base class for types
    
    def isValueType():
        return False

    def isListType():
        return False
    
    def isFuncType():
        return False

    def elementType():
        return None

    def isSpecialType():
        return False