
class Node:

    def __init__(self, location:[int], kind:str):
        if len(location) != 2:
            raise Exception('location must be length 2')
        self.kind = kind
        self.location = location
        self.errorMsg = None

    def tcvisit(self, typechecker):
        raise Exception('operation not supported')

    def visit(self, visitor):
        return Exception('operation not supported')

    def toJSON(self):
        d = {}
        d['kind'] = self.kind
        d['location'] = self.location + self.location
        if self.errorMsg is not None:
            d['errorMsg'] = self.errorMsg
        return d

