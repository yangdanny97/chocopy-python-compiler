from .literal import Literal
import json

class StringLiteral(Literal):

    def __init__(self, location:[int], value:str):
        super().__init__(location, "StringLiteral")
        self.value = value

    def getPythonStr(self, builder):
        builder.addText(json.dumps(self.value))

    def visit(self, visitor):
        return visitor.StringLiteral(self)
