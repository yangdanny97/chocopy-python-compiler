from .astnodes import *
from .types import *
from .visitor import Visitor

class ClosureVisitor(Visitor):
    # mark identifiers that correspond to globals or nonlocals
    # mark declarations & parameters that capture a nested nonlocal

    # at the end of this pass, each function decl will have a freevars
    # attribute, which represents the bindings it needs from the surrounding
    # environment

    def __init__(self):
        self.globals = set()
        self.vars = []
        self.decls = []
    
    def visit(self, node: Node):
        if isinstance(node, Expr) or isinstance(node, Stmt):
            return node.postorder(self)
        return node.visit(self)

    def deduplicate(self, ids:[Identifier])->[Identifier]:
        seen = set()
        res = []
        for i in ids:
            if i.name in seen:
                continue
            seen.add(i.name)
            res.append(i)
        return res

    def Program(self, node: Program):
        for d in node.declarations:
            if isinstance(d, VarDef):
                self.globals.add(d.getIdentifier().name)
        for d in node.declarations:
            self.visit(d)
        # mark all top-level vars to be global
        self.vars = []
        for s in node.statements:
            self.visit(s)
        for v in self.vars:
            v.isGlobal = True

    def ClassDef(self, node: ClassDef):
        for d in node.declarations:
            self.visit(d)

    # given a list of potential free variables
    # return the list of variables that are not global or declared in the local context
    def process_vars(self, decls:[str],variables:[Identifier])->[Identifier]:
        # mark free variables as global
        freevars = []
        for v in variables:
            if v.name not in decls and v.name not in self.globals:
                v.isRef = True
                freevars.append(v)
            elif v.name in self.globals and not any([v.name in d for d in self.decls]):
                v.isGlobal = True
        return freevars

    def FuncDef(self, node: FuncDef):
        self.vars = []
        decls = set()
        # decls is the list of all local variable decls and function parameters
        for p in node.params:
            decls.add(p.identifier.name)
        for d in node.declarations:
            if not (isinstance(d, GlobalDecl) or isinstance(d, NonLocalDecl)):
                decls.add(d.getIdentifier().name)
        self.decls.append(decls)
        # collect all variables from function body
        for s in node.statements:
            self.visit(s)
        # get the free variables from the function body
        freevars = self.process_vars(decls, self.vars)
        # get the free variables from nested function definitions
        nested_freevars = []
        for d in node.declarations:
            self.visit(d)
            if isinstance(d, FuncDef):
                nested_freevars += d.freevars
        freevars = freevars + self.process_vars(decls, nested_freevars)
        # dedupe the list of free variables
        node.freevars = self.deduplicate(freevars)
        # mark any params and declarations that capture free vars
        freevar_names = node.getFreevarNames()
        for p in node.params:
            if p.identifier.name in freevar_names:
                p.capturedNonlocal = True
        for d in node.declarations:
            if isinstance(d, VarDef) and d.var.identifier.name in freevar_names:
                d.var.captureNonlocal = True
        self.decls.pop()
        return node
    
    def Identifier(self, node: Identifier):
        self.vars.append(node)



