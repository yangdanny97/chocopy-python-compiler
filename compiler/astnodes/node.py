from typing import List, Self, Optional


class Node:
    errorMsg: Optional[str]

    def __init__(self, location: List[int], kind: str):
        if len(location) != 2:
            raise Exception('location must be length 2')
        self.kind = kind
        self.location = location
        self.errorMsg = None

    def visit(self, visitor) -> Self:
        raise Exception('operation not supported')

    def preorder(self, visitor) -> Self:
        return self.visit(visitor)

    def postorder(self, visitor) -> Self:
        return self.visit(visitor)

    def toJSON(self, dump_location=True) -> dict:
        d = {}
        d['kind'] = self.kind
        if dump_location:
            d['location'] = self.location + self.location
        if self.errorMsg is not None:
            d['errorMsg'] = self.errorMsg
        return d
