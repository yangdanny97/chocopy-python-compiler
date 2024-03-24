from .astnodes import *
from .types import *
from .typechecker import TypeChecker
from .parser import Parser, ParseError
from .closurevisitor import ClosureVisitor
from .closuretransformer import ClosureTransformer
from .empty_list_typer import EmptyListTyper
from .nestedfunchoister import NestedFuncHoister
from .typesystem import TypeSystem
from .jvm_backend import JvmBackend
from .cil_backend import CilBackend
from .python_backend import PythonBackend
from .wasm_backend import WasmBackend
from .llvm_backend import LlvmBackend
import ast
from pathlib import Path
from typing import Optional


class Compiler:
    transformer: Optional[ClosureTransformer] = None

    def __init__(self):
        self.ts = TypeSystem()
        self.parser = Parser()
        self.typechecker = TypeChecker(self.ts)

    def parse(self, infile) -> Optional[Program]:
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
            message = "Syntax Error: {}. Line {:d} Col {:d}".format(
                str(e), e.lineno, e.offset)
            astparser.errors.append(ParseError(message))
            return None

    def closurepass(self, ast: Program):
        ClosureVisitor().visit(ast)
        NestedFuncHoister().visit(ast)
        self.transformer = ClosureTransformer()
        self.transformer.visit(ast)
        return ast

    def typecheck(self, ast: Program):
        # given an AST object, typecheck it
        # typechecking mutates the AST, adding types and errors
        self.typechecker.visit(ast)
        return ast

    def emitPython(self, ast: Program):
        backend = PythonBackend()
        backend.visit(ast)
        return backend.builder

    def emitJVM(self, main: str, ast: Program):
        self.closurepass(ast)
        EmptyListTyper().visit(ast)
        assert self.transformer is not None
        jvm_backend = JvmBackend(main, self.transformer.ts)
        jvm_backend.visit(ast)
        return jvm_backend.classes

    def emitCIL(self, main: str, ast: Program):
        self.closurepass(ast)
        EmptyListTyper().visit(ast)
        assert self.transformer is not None
        cil_backend = CilBackend(main, self.transformer.ts)
        cil_backend.visit(ast)
        return cil_backend.builder

    def emitWASM(self, main: str, ast: Program):
        self.closurepass(ast)
        EmptyListTyper().visit(ast)
        assert self.transformer is not None
        wasm_backend = WasmBackend(main, self.transformer.ts)
        wasm_backend.visit(ast)
        return wasm_backend.builder

    def emitLLVM(self, ast: Program):
        self.closurepass(ast)
        EmptyListTyper().visit(ast)
        assert self.transformer is not None
        llvm_backend = LlvmBackend(self.transformer.ts)
        llvm_backend.visit(ast)
        return llvm_backend.module
