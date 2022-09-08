from .node import Node
from typing import List


class Stmt(Node):

    def __init__(self, location: List[int], kind: str):
        super().__init__(location, kind)
        self.isReturn = False
