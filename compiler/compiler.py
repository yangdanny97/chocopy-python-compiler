from .astnodes import *
from .types import *
from .typechecker import TypeChecker
from .parser import Parser, ParseError
import ast
from pathlib import Path

class Compiler:
    def parse(self, infile, astparser: Parser) -> Node:
        # given an input file, parse it into an AST object
        lines = None
        fname = infile
        if isinstance(infile, Path):
            fname = infile.name
            with infile.open("r") as f:
                lines = "".join([line for line in f])
        else:
            with open(infile, "r") as f:
                lines = "".join([line for line in f])
        try:
            tree = ast.parse(lines)
            return astparser.visit(tree)
        except SyntaxError as e:
            e.filename = fname
            message = "Syntax Error: {}. Line {:d} Col {:d}".format(str(e), e.lineno, e.offset)
            astparser.errors.append(ParseError(message))
            return None


    def visit(self, ast: Node, tc: TypeChecker):
        # given an AST object, typecheck it
        # typechecking mutates the AST, adding types and errors
        ast.visit(tc)
