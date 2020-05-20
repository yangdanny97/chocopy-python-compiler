from .Node import Node

class Expr(Node):

    def __init__(self, location:[int], kind:str):
        super().__init__(location, kind)
        self.inferredType = None

    def toJSON(self):
        d = super().toJSON()
        if self.inferredType is not None:
            d['inferredType'] = self.inferredType.toJSON()
        return d

