from .expr import Expr

class Literal(Expr):

    def __init__(self, location:[int], kind:str):
        super().__init__(location, kind)
        self.value = None

    def toJSON(self):
        d = super().toJSON()
        if self.value is not None:
            d['value'] = self.value
        return d

