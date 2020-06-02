from .types import *
from collections import defaultdict

class TypeSystem:
    def __init__(self):
        # type hierachy: dictionary of class->superclass mappings
        self.superclasses = defaultdict(lambda: None)

        # set up default class hierarchy
        self.superclasses["object"] = None
        self.superclasses["int"] = "object"
        self.superclasses["bool"] = "object"
        self.superclasses["str"] = "object"
        self.superclasses["<None>"] = "object"
        self.superclasses["<Empty>"] = "object"

        # symbol tables for each class's methods
        self.classes = defaultdict(lambda: {})

        self.classes["object"] = {"__init__": FuncType([ObjectType()], NoneType())}
        self.classes["int"] = {"__init__": FuncType([ObjectType()], NoneType())}
        self.classes["bool"] = {"__init__": FuncType([ObjectType()], NoneType())}
        self.classes["str"] = {"__init__": FuncType([ObjectType()], NoneType())}

    def tollvm(type: SymbolType):
        pass # TODO