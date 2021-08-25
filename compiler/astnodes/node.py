
class Node:

    def __init__(self, location:[int], kind:str):
        if len(location) != 2:
            raise Exception('location must be length 2')
        self.kind = kind
        self.location = location
        self.errorMsg = None

    def visit(self, visitor):
        return Exception('operation not supported')

    def preorder(self, visitor):
        return self.visit(visitor)

    def postorder(self, visitor):
        return self.visit(visitor)

    def toJSON(self, dump_location=True):
        d = {}
        d['kind'] = self.kind
        if dump_location:
            d['location'] = self.location + self.location
        if self.errorMsg is not None:
            d['errorMsg'] = self.errorMsg
        return d

