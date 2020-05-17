import ast

class Wrapper(ast.NodeVisitor):
    """Wraps all integers in a call to Integer()"""
    def visit_Num(self, node):
        if isinstance(node.n, int):
            return {"n" : node.n}
        return node

    def visit_Expr(self, node):
        return {"expr": self.visit(node.value)}
    
    def visit_BinOp(self, node):
        return {"n":"binop", "l":self.visit(node.left), "r":self.visit(node.right)}

    def visit_Module(self, node):
        return {"body":[self.visit(b) for b in node.body]}

tree = ast.parse("1/3")
tree = Wrapper().visit(tree)
print(tree)