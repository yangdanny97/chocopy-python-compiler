from .AstNodes import *
from .Types import *
from .typechecker import TypeChecker
from .parser import Parser
from ast import *
from pathlib import Path


def parse(infile, astparser: Parser) -> Node:
    # given an input file, parse it into an AST object
    lines = None
    if isinstance(infile, Path):
        with infile.open("r") as f:
            lines = "\n".join([line for line in f])
    else:
        with open(infile, "r") as f:
            lines = "\n".join([line for line in f])
    tree = ast.parse(lines)
    return astparser.visit(py_ast_tree)


def typecheck(ast: Node, tc: TypeChecker) -> Node:
    # given an AST object, typecheck it
    ast.typecheck(tc)
