from .valuetype import ValueType

class ClassValueType(ValueType):
    def __init__(self, className:str):
        self.className = className

    def __eq__(self, other):
        if isinstance(other, ClassValueType):
            return self.className == other.className
        return False

    def isSpecialType():
        return className in ["int", "str", "bool"]
    
    def __str__(self):
        return self.className