from compiler.types.classvaluetype import ClassValueType
from .valuetype import ValueType
from .symboltype import SymbolType

class FuncType(SymbolType):
    def __init__(self, parameters:[ValueType], returnType:ValueType):
        self.parameters = parameters
        self.returnType = returnType
        self.refParams = {}
        self.freevars = [] # used in AST transformations, not printed out

    def __eq__(self, other):
        if isinstance(other, FuncType):
            return self.parameters == other.parameters and self.returnType == other.returnType
        return False

    def dropFirstParam(self):
        f = FuncType(self.parameters[1:], self.returnType)
        f.refParams = [i - 1 for i in self.refParams]
        f.freevars = self.freevars
        return f

    def getJavaSignature(self)->str:
        r = None
        if self.returnType.isNone():
            r = "V"
        else:
            r = self.returnType.getJavaSignature()
        params = []
        for i in range(len(self.parameters)):
            p = self.parameters[i]
            if i in self.refParams and isinstance(p, ClassValueType):
                sig = '[' + p.getJavaSignature(True)
            else:
                sig = p.getJavaSignature()
            params.append(sig)
            
        return "({}){}".format("".join(params), r)

    def methodEquals(self, other):
        if isinstance(other, FuncType) and len(self.parameters) > 0 and len(other.parameters) > 0:
            return self.parameters[1:] == other.parameters[1:] and self.returnType == other.returnType
        return False

    def isFuncType():
        return True

    def __str__(self):
        paramStr = ",".join([str(t) for t in self.parameters])
        return F"[{paramStr}]->{self.returnType}"
    
    def __hash__(self):
        paramStr = ",".join([str(t) for t in self.parameters])
        return (F"[{paramStr}]->{self.returnType}").__hash__()

    def toJSON(self, dump_location=True):
        return {
            "kind": "FuncType",
            "parameters": [p.toJSON(dump_location) for p in self.parameters],
            "returnType": self.returnType.toJSON(dump_location)
        }