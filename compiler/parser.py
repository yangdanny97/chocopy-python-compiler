from ast import *
from .AstNodes import *


class ParseException(Exception):
    # for AST structures that are legal in Python 3 but not in Chocopy
    def __init__(self, message, node):
        if node is not None:
            super().__init__(
                message + ". Line {:d} Col {:d}".format(node.lineno, node.col_offset))
        else:
            super().__init__(message + ".")


class Parser(NodeVisitor):
    def __init__(self):
        self.errors = []
        self.inDecl = [False]

    # collapse a list of >2 expressions separated by a
    # left-associative operator into a BinaryExpr tree
    def collapse(op: str, values: [Expr]) -> Expr:
        current = BinaryExpr(getBetweenLocation(
            values[0], values[1]), values[0], op, values[1])
        for v in values[2:]:
            current = BinaryExpr(getBetweenLocation(
                values[0], v), current, op, v)
        return current

    def getLocation(self, node):
        # get 4 item list corresponding to AST node location
        return [node.lineno, node.col_offset, node.end_lineno, node.end_col_offset]

    def getBetweenLocationPy(self, left, right):
        return [left.lineno, left.col_offset, right.end_lineno, right.end_col_offset]

    def getBetweenLocation(self, left, right):
        return left.location[:2] + right.location[2:]

    def visit(self, node):
        try:
            return super().visit(node)
        except ParseException as e:
            self.errors.append(e)
            return

    def inDecl(self):
        # return if visitor is inside a class or function declaration
        return self.inDecl[-1]

    # see https://greentreesnakes.readthedocs.io/en/latest/nodes.html
    # and https://docs.python.org/3/library/ast.html

    def visit_Module(self, node):
        location = self.getLocation(node)
        body = [self.visit(b) for b in node.body]
        declarations = []
        statements = []
        decl = True
        for i in range(len(body)):
            b = body[i]
            if isinstance(b, Declaration):
                declarations.append(b)
            else:
                statements.append(b)
            if not isinstance(b, Declaration):
                decl = False
            if isinstance(b, Declaration) and decl == False:
                raise ParseException(
                    "All declarations must come before statements", node.body[i])
        return Program(location, declarations, statements, [])  # TODO errors

    def visit_FunctionDef(self, node):
        self.inDecl.append(True)
        location = self.getLocation(node)
        # TODO
        self.inDecl.pop()

    def visit_ClassDef(self, node):
        self.inDecl.append(True)
        location = self.getLocation(node)
        # TODO
        self.inDecl.pop()

    def visit_Return(self, node):
        location = self.getLocation(node)
        if node.value == None:
            return Return(location, None)
        else:
            return Return(location, self.visit(node.value))

    def visit_Assign(self, node):
        location = self.getLocation(node)
        targets = [self.visit(t) for t in node.targets]
        return AssignStmt(location, targets, self.visit(node.value))

    def visit_AnnAssign(self, node):
        # TODO turn into VarDef, must have initializing expr
        # make sure init is Literal if not inDecl
        location = self.getLocation(node)

    def visit_While(self, node):
        location = self.getLocation(node)
        if node.orelse:
            raise ParseException("Cannot have else in while", node)
        condition = self.visit(node.test)
        body = [self.visit(b) for b in node.body]
        return WhileStmt(location, condition, body)

    def visit_For(self, node):
        location = self.getLocation(node)
        if node.orelse:
            raise ParseException("Cannot have else in for", node)
        identifier = self.visit(node.target)
        iterable = self.visit(node.iter)
        body = [self.visit(b) for b in node.body]
        return ForStmt(location, identifier, iterable, body)

    def visit_If(self, node):
        location = self.getLocation(node)
        condition = self.visit(node.test)
        then_body = [self.visit(b) for b in node.body]
        else_body = [self.visit(o) for o on node.orelse] 
        return IfStmt(location, condition, then_body, else_body)

    def visit_Global(self, node):
        location = self.getLocation(node)
        if len(node.names) != 1:
            raise ParseException(
                "Only one identifier is allowed per global declaration", node)
        # the ID starts 7 characters to the right
        idLoc = [location[0], location[1] + 7, location[2], location[3]]
        identifier = Identifier(idLoc, node.names[0])
        return GlobalDecl(location, identifier)

    def visit_Nonlocal(self, node):
        location = self.getLocation(node)
        if len(node.names) != 1:
            raise ParseException(
                "Only one identifier is allowed per nonlocal declaration", node)
        # the ID starts 7 characters to the right
        idLoc = [location[0], location[1] + 7, location[2], location[3]]
        identifier = Identifier(idLoc, node.names[0])
        return NonLocalDecl(location, identifier)

    def visit_Expr(self, node):
        # this is a Stmt that evaluates an Expr
        location = self.getLocation(node)
        return ExprStmt(location, self.visit(node.value))

    def visit_Pass(self, node):
        # removed by any AST constructors that take in [Stmt]
        return None

    def visit_BoolOp(self, node):
        values = [self.visit(v) for v in node.values]
        op = self.visit(node.op)
        return self.collapse(op, values)

    def visit_BinOp(self, node):
        location = self.getLocation(node)
        return BinaryExpr(location, self.visit(node.left),
                          self.visit(node.op), self.visit(node.right))

    def visit_UnaryOp(self, node):
        location = self.getLocation(node)
        return UnaryExpr(location, self.visit(node.op), self.visit(node.operand))

    def visit_IfExp(self, node):
        location = self.getLocation(node)
        condition = self.visit(node.test)
        then_body = self.visit(node.body)
        else_body = self.visit(node.orelse)
        return IfExpr(location, condition, then_body, else_body)

    def visit_Call(self, node):
        location = self.getLocation(node)
        # TODO

    def visit_Constant(self, node):
        # support for Python 3.8
        location = self.getLocation(node)
        if isinstance(node.value, int):
            return IntegerLiteral(location, node.n)
        elif isinstance(node.value, str) and node.kind == None:
            return StringLiteral(location, node.value)
        elif isinstance(node.value, bool):
            return BooleanLiteral(location, node.value)
        elif node.value == None:
            return NoneLiteral(location)
        else:
            raise ParseError("Constant data type not supported", node)

    def visit_Attribute(self, node):
        location = self.getLocation(node)
        # TODO

    def visit_Subscript(self, node):
        location = self.getLocation(node)
        return IndexExpr(location, self.visit(node.value), self.visit(node.slice))

    def visit_Name(self, node):
        location = self.getLocation(node)
        return Identifier(location, node.id)

    def visit_Num(self, node):
        location = self.getLocation(node)
        if not isinstance(node.n, int):
            raise ParseException("Only integers are allowed", node)
        return IntegerLiteral(location, node.n)

    def visit_Str(self, node):
        location = self.getLocation(node)
        return StringLiteral(location, node.n)

    def visit_List(self, node):
        location = self.getLocation(node)

    def visit_NameConstant(self, node):
        location = self.getLocation(node)
        if node.value == None:
            return NoneLiteral(location)
        else:
            return BooleanLiteral(location, node.value)

    def visit_Index(self, node):
        return self.visit(node.value)

    def visit_arguments(self, node):
        location = self.getLocation(node)
        # TODO

    def visit_arg(self, node):
        # type annotation is either Str(s) or Name(id)
        location = self.getLocation(node)
        # TODO

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

    def visit_Invert(self, node):
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

    # unsupported nodes

    def visit_Expression(self, node):
        raise ParseException("Unsupported node", node)

    def visit_AsyncFunctionDef(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Delete(self, node):
        raise ParseException("Unsupported node", node)

    def visit_AsyncFor(self, node):
        raise ParseException("Unsupported node", node)

    def visit_AugAssign(self, node):
        raise ParseException("Unsupported node", node)

    def visit_With(self, node):
        raise ParseException("Unsupported node", node)

    def visit_AsyncWith(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Raise(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Try(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Assert(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Import(self, node):
        raise ParseException("Unsupported node", node)

    def visit_ImportFrom(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Break(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Continue(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Lambda(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Dict(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Set(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Bytes(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Ellipses(self, node):
        raise ParseException("Unsupported node", node)

    def visit_ListComp(self, node):
        raise ParseException("Unsupported node", node)

    def visit_SetComp(self, node):
        raise ParseException("Unsupported node", node)

    def visit_DictComp(self, node):
        raise ParseException("Unsupported node", node)

    def visit_GeneratorExp(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Await(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Yield(self, node):
        raise ParseException("Unsupported node", node)

    def visit_YieldFrom(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Compare(self, node):
        raise ParseException("Unsupported node", node)

    def visit_FormattedValue(self, node):
        raise ParseException("Unsupported node", node)

    def visit_JoinedStr(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Starred(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Tuple(self, node):
        raise ParseException("Unsupported node", node)

    def visit_AugLoad(self, node):
        raise ParseException("Unsupported node", node)

    def visit_AugStore(self, node):
        raise ParseException("Unsupported node", node)

    def visit_MatMult(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Div(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Slice(self, node):
        raise ParseException("Unsupported node", node)

    def visit_ExtSlice(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Pow(self, node):
        raise ParseException("Unsupported node", node)

    def visit_LShift(self, node):
        raise ParseException("Unsupported node", node)

    def visit_RShift(self, node):
        raise ParseException("Unsupported node", node)

    def visit_BitOr(self, node):
        raise ParseException("Unsupported node", node)

    def visit_BitXor(self, node):
        raise ParseException("Unsupported node", node)

    def visit_BitAnd(self, node):
        raise ParseException("Unsupported node", node)

    def visit_UAdd(self, node):
        raise ParseException("Unsupported node", node)

    def visit_USub(self, node):
        raise ParseException("Unsupported node", node)

    def visit_IsNot(self, node):
        raise ParseException("Unsupported node", node)

    def visit_In(self, node):
        raise ParseException("Unsupported node", node)

    def visit_NotIn(self, node):
        raise ParseException("Unsupported node", node)

    def visit_ExceptHandlerattributes(self, node):
        raise ParseException("Unsupported node", node)

    def visit_TypeIgnore(self, node):
        raise ParseException("Unsupported node", node)

    def visit_FunctionType(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Suite(self, node):
        raise ParseException("Unsupported node", node)

    def visit_Interactive(self, node):
        raise ParseException("Unsupported node", node)

    def visit_alias(self, node):
        raise ParseException("Unsupported node", node)

    def visit_keyword(self, node):
        raise ParseException("Unsupported node", node)

    def visit_comprehension(self, node):
        raise ParseException("Unsupported node", node)

    def visit_withitem(self, node):
        raise ParseException("Unsupported node", node)

    def visit_NamedExpr(self, node):
        raise ParseException("Unsupported node", node)

    # expression contexts - do nothing

    def visit_Load(self, node):
        pass

    def visit_Store(self, node):
        pass

    def visit_Del(self, node):
        pass

    def visit_Param(self, node):
        pass
