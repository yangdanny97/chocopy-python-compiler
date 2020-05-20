from .Node import Node

class CompilerError(Node):

    def __init__(self, location:[int], message:str, syntax:bool):
        super().__init__(location, "CompilerError")
        self.message = message
        self.syntax = syntax

    def typecheck(self, typechecker):
        pass

    def toJSON(self):
        d = super().toJSON()
        d["message"] = self.message
        d["syntax"] = self.syntax
        return d
