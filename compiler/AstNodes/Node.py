
class Node:

    def __init__(self, location:[int], kind:str):
        self.kind = kind
        self.location = location
        self.errorMsg = None

    def typecheck(self, typechecker):
        raise Exception('operation not supported')

    def toJSON(self):
        d = {}
        d['kind'] = kind
        d['location'] = location
        return d

