from .astnodes import *
from .types import *
from .typechecker import TypeChecker
from .parser import Parser, ParseException
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
            astparser.errors.append(ParseException(message))
            return None


    def typecheck(self, ast: Node, tc: TypeChecker) -> Node:
        # given an AST object, typecheck it
        ast.typecheck(tc)
