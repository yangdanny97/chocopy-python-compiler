from compiler.types.classvaluetype import ClassValueType
from .valuetype import ValueType
from .symboltype import SymbolType
from .varinstance import VarInstance
from typing import List, Dict
from llvmlite import ir


class FuncType(SymbolType):
    refParams: Dict[int, VarInstance]
    freevars: list

    def __init__(self, parameters: List[ValueType], returnType: ValueType):
        self.parameters = parameters
        self.returnType = returnType
        self.refParams = {}
        self.freevars = []

    def __eq__(self, other):
        if isinstance(other, FuncType):
            return self.parameters == other.parameters and self.returnType == other.returnType
        return False

    def dropFirstParam(self):
        f = FuncType(self.parameters[1:], self.returnType)
        f.refParams = {i - 1: v for i, v in self.refParams.items()}
        f.freevars = self.freevars
        return f

    def getCILName(self) -> str:
        raise Exception("unsupported")

    def getCILSignature(self, name: str) -> str:
        params = []
        for i in range(len(self.parameters)):
            p = self.parameters[i]
            if i in self.refParams and isinstance(p, ClassValueType):
                sig = p.getCILSignature() + "&"
            else:
                sig = p.getCILSignature()
            params.append(sig)
        paramSig = ", ".join(params)
        return f"{self.returnType.getCILSignature()} {name}({paramSig})"

    def getJavaSignature(self) -> str:
        r = None
        if self.returnType.isNone():
            r = "V"
        else:
            r = self.returnType.getJavaSignature(False)
        params = []
        for i in range(len(self.parameters)):
            p = self.parameters[i]
            if i in self.refParams and isinstance(p, ClassValueType):
                sig = '[' + p.getJavaSignature(True)
            else:
                sig = p.getJavaSignature(False)
            params.append(sig)
        return "({}){}".format("".join(params), r)

    def getWasmSignature(self, names=None) -> str:
        params = []
        for i in range(len(self.parameters)):
            p = self.parameters[i]
            paramName = ("$" + names[i]) if names else ""
            if i in self.refParams and isinstance(p, ClassValueType):
                sig = f"(param {paramName} i32)"
            else:
                sig = f"(param {paramName} {p.getWasmName()})"
            params.append(sig)
        params = " ".join(params)
        result = "" if self.returnType.isNone(
        ) else f" (result {self.returnType.getWasmName()})"
        return params + result

    def methodEquals(self, other) -> bool:
        if isinstance(other, FuncType) and len(self.parameters) > 0 and len(other.parameters) > 0:
            return self.parameters[1:] == other.parameters[1:] and self.returnType == other.returnType
        return False

    def isFuncType(self) -> bool:
        return True

    def __str__(self):
        paramStr = ",".join([str(t) for t in self.parameters])
        return F"[{paramStr}]->{self.returnType}"

    def __hash__(self):
        paramStr = ",".join([str(t) for t in self.parameters])
        return (F"[{paramStr}]->{self.returnType}").__hash__()

    def toJSON(self, dump_location=True) -> dict:
        return {
            "kind": "FuncType",
            "parameters": [p.toJSON(dump_location) for p in self.parameters],
            "returnType": self.returnType.toJSON(dump_location)
        }

    def getLLVMType(self) -> ir.FunctionType:
        params = []
        for i in range(len(self.parameters)):
            p = self.parameters[i]
            if i in self.refParams and isinstance(p, ClassValueType):
                sig = p.getLLVMType().as_pointer()
            else:
                sig = p.getLLVMType()
            params.append(sig)
        returnType = self.returnType.getLLVMType()
        return ir.FunctionType(returnType, params)
