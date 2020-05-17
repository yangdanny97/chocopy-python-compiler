from Expr import Expr

class Literal(Expr):

    def __init__(self, location:[int], kind:str):
        super().__init__(self, location, kind)
        self.value = None

    def toJSON(self):
        d = super().toJSON(self)
        d['value'] = self.value
        return d

