from .node import Node

class Declaration(Node):

    def __init__(self, location:[int], kind:str):
        super().__init__(location, kind)
