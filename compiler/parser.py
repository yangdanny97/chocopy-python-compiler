from ast import *

class ParseException(Exception):
    def __init__(self, message, node):
        super().__init__(message + " at line {} col {}".format(node.lineno, node.col_offset))

class Parser(NodeVisitor):
    def __init__(self):
        pass

    # see https://greentreesnakes.readthedocs.io/en/latest/nodes.html

    def visit_Module(self, node):
        pass

    def visit_FunctionDef(self, node):
        pass

    def visit_ClassDef(self, node):
        pass

    def visit_Return(self, node):
        pass

    def visit_Assign(self, node):
        pass

    def visit_While(self, node):
        pass

    def visit_If(self, node):
        pass

    def visit_Global(self, node):
        pass

    def visit_Nonlocal(self, node):
        pass

    def visit_Expr(self, node):
        pass

    def visit_Pass(self, node):
        pass

    def visit_BoolOp(self, node):
        pass

    def visit_NamedExpr(self, node):
        pass

    def visit_BinOp(self, node):
        pass

    def visit_UnaryOp(self, node):
        pass

    def visit_IfExp(self, node):
        pass

    def visit_Call(self, node):
        pass

    def visit_Constant(self, node):
        pass

    def visit_Attribute(self, node):
        pass

    def visit_Subscript(self, node):
        pass

    def visit_Name(self, node):
        pass

    def visit_Num(self, node):
        pass

    def visit_Str(self, node):
        pass

    def visit_List(self, node):
        pass

    def visit_NameConstant(self, node):
        pass

    def visit_Param(self, node):
        pass

    def visit_Index(self, node):
        pass

    def visit_And(self, node):
        pass

    def visit_Or(self, node):
        pass

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

    def visit_arguments(self, node):
        pass

    def visit_arg(self, node):
        # type annotation is either Str(s) or Name(id)
        pass

    def visit_Expression(self, node):
        raise ParseException("Unsupported node ", node)
    
    def visit_AsyncFunctionDef(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Delete(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_AsyncFor(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_AugAssign(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_AnnAssign(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_For(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_With(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_AsyncWith(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Raise(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Try(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Assert(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Import(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_ImportFrom(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Break(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Continue(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Lambda(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Dict(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Set(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Bytes(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Ellipses(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_ListComp(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_SetComp(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_DictComp(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_GeneratorExp(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Await(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Yield(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_YieldFrom(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Compare(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_FormattedValue(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_JoinedStr(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Starred(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Tuple(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Load(self, node):
        pass

    def visit_Store(self, node):
        pass

    def visit_Del(self, node):
        pass

    def visit_AugLoad(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_AugStore(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_MatMult(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Div(self, node):
        raise ParseException("Unsupported node ", node)

     def visit_Slice(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_ExtSlice(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Pow(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_LShift(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_RShift(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_BitOr(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_BitXor(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_BitAnd(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_UAdd(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_USub(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_IsNot(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_In(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_NotIn(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_ExceptHandlerattributes (self, node):
        raise ParseException("Unsupported node ", node)

    def visit_TypeIgnore(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_FunctionType(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Suite(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_Interactive(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_alias(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_keyword(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_comprehension(self, node):
        raise ParseException("Unsupported node ", node)

    def visit_withitem(self, node):
        raise ParseException("Unsupported node ", node)