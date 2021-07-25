from .node import Node

class CompilerError(Node):

    def __init__(self, location:[int], message:str, syntax:bool=False):
        super().__init__(location, "CompilerError")
        self.message = message
        self.syntax = syntax

    def getPythonStr(self, builder):
        pass

    def toJSON(self, dump_location=True):
        d = super().toJSON(dump_location)
        d["message"] = self.message
        return d
