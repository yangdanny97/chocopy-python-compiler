from .astnodes import *
from .types import *
from .typechecker import TypeChecker
from .parser import Parser, ParseError
from .closurevisitor import ClosureVisitor
from .closuretransformer import ClosureTransformer 
from .nestedfunchoister import NestedFuncHoister
from .typesystem import TypeSystem
from .jvm_backend import JvmBackend
import ast
from pathlib import Path

class Compiler:
    def __init__(self):
        self.ts = TypeSystem()
        self.parser = Parser()
        self.typechecker = TypeChecker(self.ts)

    def parse(self, infile) -> Node:
        astparser = self.parser
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

    def closurepass(self, ast: Node):
        ast.visit(ClosureVisitor())
        ast.visit(NestedFuncHoister())
        ast.visit(ClosureTransformer())
        ast.visit(TypeChecker(TypeSystem()))

    def typecheck(self, ast: Node):
        # given an AST object, typecheck it
        # typechecking mutates the AST, adding types and errors
        ast.visit(self.typechecker)

    def emitJVM(self, main:str, ast: Node):
        jvm_backend = JvmBackend(main, self.typechecker.ts)
        jvm_backend.visit(ast)
        return jvm_backend.builder
        
    
