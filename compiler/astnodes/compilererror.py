from .node import Node

class CompilerError(Node):

    def __init__(self, location:[int], message:str, syntax:bool=False):
        super().__init__(location, "CompilerError")
        self.message = message
        self.syntax = syntax

    def toJSON(self):
        d = super().toJSON()
        d["message"] = self.message
        return d
