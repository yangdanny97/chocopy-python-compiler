from .AstNodes import *
from .Types import *
from .TypeChecker import TypeChecker
from .Parser import Parser
from ast import *

def parse(infile: str) -> Node:
    # given an input file, parse it into an AST object
    lines = None
    with open(infile) as f:
        lines = "\n".join([line for line in f])
    tree = ast.parse(lines)
    return Parser().visit(py_ast_tree)

def typecheck(ast: Node) -> Node:
    # given an AST object, typecheck it
    ast.typecheck(TypeChecker())
