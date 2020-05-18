from .Node import Node

class Expr(Node):

    def __init__(self, location:[int], kind:str):
        super().__init__(self, location, kind)
        self.inferredType = None

    def toJSON(self):
        d = super().toJSON(self)
        if self.inferredType is not None:
            d['inferredType'] = self.inferredType.toJSON()
        return d

