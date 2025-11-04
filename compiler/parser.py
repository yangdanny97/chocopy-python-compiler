from .astnodes import *
import ast
import typing


class ParseError(Exception):
    # for AST structures that are legal in Python 3 but not in Chocopy
    def __init__(self, message, node=None):
        if node is not None:
            if hasattr(node, "lineno"):
                super().__init__(
                    message + ". Line {:d} Col {:d}".format(node.lineno, node.col_offset))
                return
        super().__init__(message + ".")


class Parser(ast.NodeVisitor):
    def __init__(self):
        self.errors = []

    # reduce a list of >2 expressions separated by a
    # left-associative operator into a BinaryExpr tree
    def binaryReduce(self, op: str, values: typing.List[Expr]) -> BinaryExpr:
        current = BinaryExpr(values[0].location, values[0], op, values[1])
        for v in values[2:]:
            current = BinaryExpr(values[0].location, current, op, v)
        return current

    def getLocation(self, node: ast.AST) -> typing.List[int]:
        # input is Python AST node
        # get 2 item list corresponding to AST node starting location
        # make columns 1-indexed
        # pyrefly: ignore [missing-attribute, missing-attribute]
        return [node.lineno, node.col_offset + 1]

    def visit(self, node: ast.AST) -> typing.Any:
        try:
            return super().visit(node)
        except ParseError as e:
            self.errors.append(e)
            return

    # process python AST nodes into chocopy type annotations
    def getTypeAnnotation(self, node: ast.expr) -> TypeAnnotation:
        location = self.getLocation(node)
        if isinstance(node, ast.List):
            if len(node.elts) > 1:
                raise ParseError("Unsupported List type annotation", node)
            return ListType(location, self.getTypeAnnotation(node.elts[0]))
        elif isinstance(node, ast.Name):
            return ClassType(location, node.id)
        elif isinstance(node, ast.Str):
            # pyrefly: ignore [bad-argument-type, deprecated]
            return ClassType(location, node.s)
        else:
            raise ParseError("Unsupported type annotation", node)

    # see https://greentreesnakes.readthedocs.io/en/latest/nodes.html
    # and https://docs.python.org/3/library/ast.html

    def visit_Module(self, node: ast.Module) -> Program:
        location = [1, 1]
        if hasattr(node, "type_ignores") and node.type_ignores:
            raise ParseError("Cannot ignore type", node)
        body = [self.visit(b) for b in node.body]
        declarations = []
        statements = []
        decl = True
        for i in range(len(body)):
            b = body[i]
            if isinstance(b, Declaration):
                if isinstance(b, VarDef):
                    if not isinstance(b.value, Literal):
                        raise ParseError(
                            "Global variables can only be initialized with literals", node.body[i])
                if (isinstance(body[i], GlobalDecl) or isinstance(body[i], NonLocalDecl)):
                    raise ParseError(
                        "Expected function, class, or variable declaration", node.body[i])
                if not decl:
                    raise ParseError(
                        "All declarations must come before statements", node.body[i])
                declarations.append(b)
            elif b is None or isinstance(b, Stmt):
                statements.append(b)
                decl = False
            else:
                raise ParseError(
                    "Expected declaration or statement", node.body[i])
        if declarations:
            location = declarations[0].location
        return Program(location, declarations, statements, Errors([0, 0], []))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> FuncDef:
        if node.decorator_list:
            raise ParseError("Unsupported decorator list",
                             node.decorator_list[0])
        location = self.getLocation(node)
        identifier = Identifier([location[0], location[1] + 4], node.name)
        arguments = self.visit(node.args)
        body = [self.visit(b) for b in node.body]
        declarations = []
        statements = []
        decl = True
        for i in range(len(body)):
            b = body[i]
            if isinstance(b, Declaration):
                if isinstance(b, ClassDef):
                    raise ParseError(
                        "Inner classes are unsupported", node.body[i])
                if not decl:
                    raise ParseError(
                        "All declarations must come before statements", node.body[i])
                declarations.append(b)
            elif b is None or isinstance(b, Stmt):
                statements.append(b)
                decl = False
            else:
                raise ParseError(
                    "Expected declaration or statement", node.body[i])
        returns = None
        if node.name == "__init__" and node.returns is not None:
            raise ParseError("__init__ cannot have a return type", node)
        if node.returns is None:
            returns = ClassType(location, "<None>")
        else:
            returns = self.getTypeAnnotation(node.returns)
        return FuncDef(location, identifier, arguments, returns, declarations, statements)

    def visit_ClassDef(self, node: ast.ClassDef) -> ClassDef:
        location = self.getLocation(node)
        identifier = Identifier([location[0], location[1] + 6], node.name)
        if len(node.bases) > 1:
            raise ParseError(
                "Multiple inheritance is unsupported", node.bases[1])
        base = None
        if len(node.bases) == 0:
            base = Identifier([location[0], location[1] +
                               7 + len(node.name)], "object")
        else:
            base = self.visit(node.bases[0])
        if node.keywords:
            raise ParseError("Unsupported keywords", node.keywords[0])
        if node.decorator_list:
            raise ParseError("Unsupported decorator list",
                             node.decorator_list[0])
        body = [self.visit(b) for b in node.body]
        # allow class bodies that only contain a single pass
        if len(body) == 1 and body[0] is None:
            body = []
        else:
            for i in range(len(body)):
                if not isinstance(body[i], Declaration):
                    raise ParseError("Expected declaration", node.body[i])
                if (isinstance(body[i], ClassDef) or isinstance(body[i], GlobalDecl) or isinstance(body[i], NonLocalDecl)):
                    raise ParseError(
                        "Expected attribute or method declaration", node.body[i])
        return ClassDef(location, identifier, base, body)

    def visit_Return(self, node: ast.Return) -> ReturnStmt:
        location = self.getLocation(node)
        if node.value is None:
            return ReturnStmt(location, None)
        else:
            return ReturnStmt(location, self.visit(node.value))

    def visit_Assign(self, node: ast.Assign) -> AssignStmt:
        location = self.getLocation(node)
        targets = [self.visit(t) for t in node.targets]
        return AssignStmt(location, targets, self.visit(node.value))

    def visit_AnnAssign(self, node: ast.AnnAssign) -> VarDef:
        if not node.value:
            raise ParseError("Expected initializing value", node)
        if not hasattr(node, "annotation") or not node.annotation:
            raise ParseError("Missing type annotation", node)
        if not node.simple:
            raise ParseError("Expected variable", node.target)
        location = self.getLocation(node)
        var = TypedVar(self.getLocation(node.target),
                       self.visit(node.target), self.getTypeAnnotation(node.annotation))
        value = self.visit(node.value)
        if not isinstance(value, Literal):
            raise ParseError("Expected literal value", node.value)
        return VarDef(location, var, value)

    def visit_While(self, node: ast.While) -> WhileStmt:
        location = self.getLocation(node)
        if node.orelse:
            raise ParseError("Cannot have else in while", node)
        condition = self.visit(node.test)
        body = [self.visit(b) for b in node.body]
        for s in body:
            if isinstance(s, Declaration):
                raise ParseError("Illegal declaration", node)
        return WhileStmt(location, condition, body)

    def visit_For(self, node: ast.For) -> ForStmt:
        location = self.getLocation(node)
        if node.orelse:
            raise ParseError("Cannot have else in for", node)
        identifier = self.visit(node.target)
        iterable = self.visit(node.iter)
        body = [self.visit(b) for b in node.body]
        for s in body:
            if isinstance(s, Declaration):
                raise ParseError("Illegal declaration", node)
        return ForStmt(location, identifier, iterable, body)

    def visit_If(self, node: ast.If) -> IfStmt:
        location = self.getLocation(node)
        condition = self.visit(node.test)
        then_body = [self.visit(b) for b in node.body]
        if not node.orelse:
            node.orelse = []
        else_body = [self.visit(o) for o in node.orelse]
        for s in then_body + else_body:
            if isinstance(s, Declaration):
                raise ParseError("Illegal declaration", node)
        return IfStmt(location, condition, then_body, else_body)

    def visit_Global(self, node: ast.Global) -> GlobalDecl:
        location = self.getLocation(node)
        if len(node.names) != 1:
            raise ParseError(
                "Only one identifier is allowed per global declaration", node)
        # the ID starts 7 characters to the right
        idLoc = [location[0], location[1] + 7]
        identifier = Identifier(idLoc, node.names[0])
        return GlobalDecl(location, identifier)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> NonLocalDecl:
        location = self.getLocation(node)
        if len(node.names) != 1:
            raise ParseError(
                "Only one identifier is allowed per nonlocal declaration", node)
        # the ID starts 7 characters to the right
        idLoc = [location[0], location[1] + 7]
        identifier = Identifier(idLoc, node.names[0])
        return NonLocalDecl(location, identifier)

    def visit_Expr(self, node: ast.Expr) -> ExprStmt:
        # this is a Stmt that evaluates an Expr
        location = self.getLocation(node)
        val = self.visit(node.value)
        return ExprStmt(location, val)

    def visit_Pass(self, node: ast.Pass) -> None:
        # removed by any AST constructors that take in [Stmt]
        return None

    def visit_BoolOp(self, node: ast.BoolOp) -> BinaryExpr:
        values = [self.visit(v) for v in node.values]
        op = self.visit(node.op)
        return self.binaryReduce(op, values)

    def visit_BinOp(self, node: ast.BinOp) -> BinaryExpr:
        left = self.visit(node.left)
        right = self.visit(node.right)
        location = self.getLocation(node)
        return BinaryExpr(location, left, self.visit(node.op), right)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> UnaryExpr:
        operand = self.visit(node.operand)
        location = self.getLocation(node)
        return UnaryExpr(location, self.visit(node.op), operand)

    def visit_IfExp(self, node: ast.IfExp) -> IfExpr:
        location = self.getLocation(node)
        condition = self.visit(node.test)
        then_body = self.visit(node.body)
        else_body = self.visit(node.orelse)
        return IfExpr(location, condition, then_body, else_body)

    def visit_Call(self, node: ast.Call) -> Expr:
        location = self.getLocation(node)
        function = self.visit(node.func)
        if node.keywords:
            raise ParseError("Keyword args are not supported", node)
        arguments = [self.visit(a) for a in node.args]
        if isinstance(function, MemberExpr):
            return MethodCallExpr(location, function, arguments)
        if isinstance(function, Identifier):
            return CallExpr(location, function, arguments)
        raise ParseError("Invalid receiver of call", node.func)

    def visit_Constant(self, node: ast.Constant) -> Expr:
        # support for Python 3.8
        location = self.getLocation(node)
        if isinstance(node.value, bool):
            return BooleanLiteral(location, node.value)
        elif isinstance(node.value, int):
            return IntegerLiteral(location, node.value)
        elif isinstance(node.value, str) and node.kind is None:
            return StringLiteral(location, node.value)
        elif node.value is None:
            return NoneLiteral(location)
        else:
            raise ParseError("Unsupported constant", node)

    def visit_Compare(self, node: ast.Compare) -> BinaryExpr:
        if len(node.ops) > 1 or len(node.comparators) > 1:
            raise ParseError("Unsupported compare between > 2 things", node)
        location = self.getLocation(node)
        left = self.visit(node.left)
        operator = self.visit(node.ops[0])
        right = self.visit(node.comparators[0])
        return BinaryExpr(location, left, operator, right)

    def visit_Attribute(self, node: ast.Attribute) -> MemberExpr:
        location = self.getLocation(node)
        obj = self.visit(node.value)
        member = Identifier(location, node.attr)
        return MemberExpr(location, obj, member)

    def visit_Subscript(self, node: ast.Subscript) -> IndexExpr:
        location = self.getLocation(node)
        return IndexExpr(location, self.visit(node.value), self.visit(node.slice))

    def visit_Name(self, node: ast.Name) -> Identifier:
        location = self.getLocation(node)
        return Identifier(location, node.id)

    def visit_Num(self, node: ast.Num) -> IntegerLiteral:
        location = self.getLocation(node)
        # pyrefly: ignore [deprecated]
        if not isinstance(node.n, int):
            raise ParseError("Only integers are supported", node)
        return IntegerLiteral(location, node.n)

    def visit_Str(self, node: ast.Str) -> StringLiteral:
        location = self.getLocation(node)
        # pyrefly: ignore [bad-argument-type, deprecated]
        return StringLiteral(location, node.s)

    def visit_List(self, node: ast.List) -> ListExpr:
        location = self.getLocation(node)
        elements = [self.visit(e) for e in node.elts]
        return ListExpr(location, elements)

    def visit_NameConstant(self, node: ast.NameConstant) -> Expr:
        location = self.getLocation(node)
        if node.value is None:
            return NoneLiteral(location)
        elif isinstance(node.value, bool):
            return BooleanLiteral(location, node.value)
        else:
            raise ParseError("Unsupported name constant", node)

    def visit_arguments(self, node: ast.arguments) -> list:
        if node.vararg:
            raise ParseError("Unsupported vararg", node.vararg)
        if node.kwarg:
            raise ParseError("Unsupported kwarg", node.kwarg)
        if node.defaults or node.kw_defaults:
            raise ParseError("Default arguments are unsupported", node)
        args = []
        if hasattr(node, "posonlyargs"):
            args = node.posonlyargs
        args = args + node.args
        args = [self.visit(a) for a in args]
        return args

    def visit_arg(self, node: ast.arg) -> TypedVar:
        # type annotation is either Str(s) or Name(id)
        if not hasattr(node, "annotation") or not node.annotation:
            raise ParseError("Missing type annotation", node)
        location = self.getLocation(node)
        identifier = Identifier(location, node.arg)
        annotation = self.getTypeAnnotation(node.annotation)
        return TypedVar(location, identifier, annotation)

    def visit_Assert(self, node: ast.Assert) -> ExprStmt:
        location = self.getLocation(node)
        func = Identifier(location, "__assert__")
        return ExprStmt(location, CallExpr(location, func, [self.visit(node.test)]))

    # operators

    def visit_And(self, node):
        return "and"

    def visit_Or(self, node):
        return "or"

    def visit_Add(self, node):
        return "+"

    def visit_Sub(self, node):
        return "-"

    def visit_Mult(self, node):
        return "*"

    def visit_Mod(self, node):
        return "%"

    def visit_FloorDiv(self, node):
        return "//"

    def visit_USub(self, node):
        return "-"

    def visit_Not(self, node):
        return "not"

    def visit_Eq(self, node):
        return "=="

    def visit_NotEq(self, node):
        return "!="

    def visit_Lt(self, node):
        return "<"

    def visit_LtE(self, node):
        return "<="

    def visit_Gt(self, node):
        return ">"

    def visit_GtE(self, node):
        return ">="

    def visit_Is(self, node):
        return "is"

    # Unsupported node: TODO improve error messages

    def visit_Expression(self, node):
        raise ParseError("Unsupported", node)

    def visit_AsyncFunctionDef(self, node):
        raise ParseError("Unsupported", node)

    def visit_Delete(self, node):
        raise ParseError("Unsupported", node)

    def visit_AsyncFor(self, node):
        raise ParseError("Unsupported", node)

    def visit_AugAssign(self, node):
        raise ParseError("Unsupported", node)

    def visit_With(self, node):
        raise ParseError("Unsupported", node)

    def visit_AsyncWith(self, node):
        raise ParseError("Unsupported", node)

    def visit_Raise(self, node):
        raise ParseError("Unsupported", node)

    def visit_Try(self, node):
        raise ParseError("Unsupported", node)

    def visit_Import(self, node):
        raise ParseError("Unsupported", node)

    def visit_ImportFrom(self, node):
        raise ParseError("Unsupported", node)

    def visit_Break(self, node):
        raise ParseError("Unsupported", node)

    def visit_Continue(self, node):
        raise ParseError("Unsupported", node)

    def visit_Lambda(self, node):
        raise ParseError("Unsupported", node)

    def visit_Dict(self, node):
        raise ParseError("Unsupported", node)

    def visit_Set(self, node):
        raise ParseError("Unsupported", node)

    def visit_Bytes(self, node):
        raise ParseError("Unsupported", node)

    def visit_Ellipses(self, node):
        raise ParseError("Unsupported", node)

    def visit_ListComp(self, node):
        raise ParseError("Unsupported", node)

    def visit_SetComp(self, node):
        raise ParseError("Unsupported", node)

    def visit_DictComp(self, node):
        raise ParseError("Unsupported", node)

    def visit_GeneratorExp(self, node):
        raise ParseError("Unsupported", node)

    def visit_Await(self, node):
        raise ParseError("Unsupported", node)

    def visit_Yield(self, node):
        raise ParseError("Unsupported", node)

    def visit_YieldFrom(self, node):
        raise ParseError("Unsupported", node)

    def visit_FormattedValue(self, node):
        raise ParseError("Unsupported", node)

    def visit_JoinedStr(self, node):
        raise ParseError("Unsupported", node)

    def visit_Starred(self, node):
        raise ParseError("Unsupported", node)

    def visit_Tuple(self, node):
        raise ParseError("Unsupported", node)

    def visit_AugLoad(self, node):
        raise ParseError("Unsupported", node)

    def visit_AugStore(self, node):
        raise ParseError("Unsupported", node)

    def visit_MatMult(self, node):
        raise ParseError("Unsupported operator: @")

    def visit_Div(self, node):
        raise ParseError("Unsupported operator: /")

    def visit_Slice(self, node):
        raise ParseError("Unsupported slice")

    def visit_ExtSlice(self, node):
        raise ParseError("Unsupported slice")

    def visit_Pow(self, node):
        raise ParseError("Unsupported operator: **")

    def visit_LShift(self, node):
        raise ParseError("Unsupported operator: <<")

    def visit_RShift(self, node):
        raise ParseError("Unsupported operator: >>")

    def visit_BitOr(self, node):
        raise ParseError("Unsupported operator: |")

    def visit_BitXor(self, node):
        raise ParseError("Unsupported operator: ^")

    def visit_BitAnd(self, node):
        raise ParseError("Unsupported operator: &")

    def visit_UAdd(self, node):
        raise ParseError("Unsupported operator: unary +")

    def visit_Invert(self, node):
        raise ParseError("Unsupported operator: ~")

    def visit_IsNot(self, node):
        raise ParseError("Unsupported operator: is not")

    def visit_In(self, node):
        raise ParseError("Unsupported operator: in")

    def visit_NotIn(self, node):
        raise ParseError("Unsupported operator: not in")

    def visit_ExceptHandlerattributes(self, node):
        raise ParseError("Unsupported", node)

    def visit_TypeIgnore(self, node):
        raise ParseError("Unsupported", node)

    def visit_FunctionType(self, node):
        raise ParseError("Unsupported", node)

    def visit_Suite(self, node):
        raise ParseError("Unsupported", node)

    def visit_Interactive(self, node):
        raise ParseError("Unsupported", node)

    def visit_alias(self, node):
        raise ParseError("Unsupported", node)

    def visit_keyword(self, node):
        raise ParseError("Unsupported", node)

    def visit_comprehension(self, node):
        raise ParseError("Unsupported", node)

    def visit_withitem(self, node):
        raise ParseError("Unsupported", node)

    def visit_NamedExpr(self, node):
        raise ParseError("Unsupported", node)

    # expression contexts - do nothing

    def visit_Load(self, node):
        pass

    def visit_Store(self, node):
        pass

    def visit_Del(self, node):
        pass

    def visit_Param(self, node):
        pass
