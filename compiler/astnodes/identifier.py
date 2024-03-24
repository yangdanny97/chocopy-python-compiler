from .expr import Expr
from typing import List, Optional
from ..types import VarInstance

CIL_KEYWORDS = set(["char", "value", "int32", "int64", "string", "long", "null"] +
                   ["add",
                    "and",
                    "any",
                    "arglist",
                    "as",
                    "be",
                    "beq",
                    "bge",
                    "bgt",
                    "ble",
                    "blt",
                    "bne",
                    "box",
                    "br",
                    "break",
                    "brfalse",
                    "brinst",
                    "brnull",
                    "brtrue",
                    "brzero",
                    "call",
                    "calli",
                    "callvirt",
                    "can",
                    "castclass",
                    "ceq",
                    "cgt",
                    "check",
                    "ckfinite",
                    "clt",
                    "constrained",
                    "conv",
                    "cpblk",
                    "cpobj",
                    "div",
                    "dup",
                    "endfault",
                    "endfilter",
                    "endfinally",
                    "execution",
                    "fault",
                    "initblk",
                    "initobj",
                    "instruction",
                    "isinst",
                    "jmp",
                    "ldarg",
                    "ldarga",
                    "ldc",
                    "ldelem",
                    "ldelema",
                    "ldfld",
                    "ldflda",
                    "ldftn",
                    "ldind",
                    "ldlen",
                    "ldloc",
                    "ldloca",
                    "ldnull",
                    "ldobj",
                    "ldsfld",
                    "ldsflda",
                    "ldstr",
                    "ldtoken",
                    "ldvirtftn",
                    "leave",
                    "localloc",
                    "mkrefany",
                    "mul",
                    "neg",
                    "newarr",
                    "newobj",
                    "no",
                    "nop",
                    "normally",
                    "not",
                    "nullcheck",
                    "of",
                    "or",
                    "ovf",
                    "part",
                    "performed",
                    "pop",
                    "rangecheck",
                    "readonly",
                    "ref",
                    "refanytype",
                    "refanyval",
                    "rem",
                    "ret",
                    "rethrow",
                    "shall",
                    "shl",
                    "shr",
                    "sizeof",
                    "skipped",
                    "specified",
                    "starg",
                    "stelem",
                    "stfld",
                    "stind",
                    "stloc",
                    "stobj",
                    "stsfld",
                    "sub",
                    "subsequent",
                    "switch",
                    "tail",
                    "throw",
                    "typecheck",
                    "un",
                    "unaligned",
                    "unbox",
                    "volatile",
                    "xor"]
                   )


class Identifier(Expr):
    varInstance: Optional[VarInstance] = None

    def __init__(self, location: List[int], name: str):
        super().__init__(location, "Identifier")
        self.name = name

    def visit(self, visitor):
        return visitor.Identifier(self)

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["name"] = self.name
        return d

    def copy(self):
        cpy = Identifier(self.location, self.name)
        cpy.inferredType = self.inferredType
        cpy.varInstance = self.varInstance
        return cpy

    def getCILName(self):
        if self.name in CIL_KEYWORDS:
            return f"'{self.name}'"
        return self.name

    def varInstanceX(self) -> VarInstance:
        assert self.varInstance is not None
        return self.varInstance
