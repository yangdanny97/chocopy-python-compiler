from .astnodes import *
from .types import *
from .typechecker import TypeChecker
from .parser import Parser
import ast
from pathlib import Path

class Compiler:
    def parse(self, infile, astparser: Parser) -> Node:
        # given an input file, parse it into an AST object
        lines = None
        if isinstance(infile, Path):
            with infile.open("r") as f:
                lines = "\n".join([line for line in f])
        else:
            with open(infile, "r") as f:
                lines = "\n".join([line for line in f])
        try:
            tree = ast.parse(lines)
            return astparser.visit(tree)
        except SyntaxError as e:
            astparser.errors.append(e)
            return None


    def typecheck(self, ast: Node, tc: TypeChecker) -> Node:
        # given an AST object, typecheck it
        ast.typecheck(tc)
