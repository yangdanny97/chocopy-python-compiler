from .valuetype import ValueType

class ClassValueType(ValueType):
    def __init__(self, className:str):
        self.className = className

    def __eq__(self, other):
        if isinstance(other, ClassValueType):
            return self.className == other.className
        return False

    def isSpecialType(self):
        return self.className in ["int", "str", "bool"]

    def getJavaName(self):
        if self.className == "bool":
            return "boolean"
        elif self.className == "str":
            return "java/lang/String"
        elif self.className == "object":
            return "java/lang/Object"
        # TODO - handle None and Empty
        elif self.className == "<None>":
            return "java/lang/Object"
        elif self.className == "<Empty>":
            raise Exception("unsupported class type")
        else:
            return self.className
    
    def __str__(self):
        return self.className

    def __hash__(self):
        return str(self).__hash__()

    def toJSON(self, dump_location=True):
        return {
            "kind": "ClassValueType",
            "className": self.className
        }
