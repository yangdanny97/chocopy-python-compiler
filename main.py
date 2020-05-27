import argparse
import json
from test import run_all_tests, run_parse_tests, run_typecheck_tests
from compiler.compiler import Compiler
from compiler.parser import Parser
from compiler.typechecker import TypeChecker
from compiler.astnodes import Node

def main():
    parser = argparse.ArgumentParser(description='Chocopy frontend')
    parser.add_argument('-t', dest='typecheck', action='store_false',
                    help='do not typecheck the AST')
    parser.add_argument('-o', dest='output', action='store_false',
                    help="do not output AST as JSON")
    parser.add_argument('--test-all', dest='testall', action='store_true',
                    help="run all test cases")
    parser.add_argument('--test-parse', dest='testparse', action='store_true',
                    help="run parser test cases")
    parser.add_argument('--test-tc', dest='testtc', action='store_true',
                    help="run typechecker test cases")
    parser.add_argument('infile', nargs='?', type=str, default=None)
    parser.add_argument('outfile', nargs='?', type=str, default=None)
    args = parser.parse_args()

    compiler = Compiler()

    if args.testall:
        run_all_tests(compiler)
        return

    if args.testparse:
        run_parse_tests(compiler)
        return

    if args.testtc:
        run_typecheck_tests(compiler)
        return

    infile = args.infile
    outfile = args.outfile
    if args.infile == None:
        print("Error: must specify input file")
        parser.print_help()
        return

    if args.outfile is None:
        if args.typecheck:
            outfile = infile + ".ast.typed"
        else:
            outfile = infile + ".ast"

    astparser = Parser()
    tree = compiler.parse(infile, astparser)

    if len(astparser.errors) > 0:
        for e in astparser.errors:
            print(e)
    elif args.typecheck:
        tc = TypeChecker()
        compiler.visit(tree, tc)
        if len(tc.errors) > 0:
            for e in astparser.errors:
                print(e)

    if args.output:
        ast_json = tree.toJSON()
        with open(outfile, "w") as f:
            json.dump(ast_json, f)
    else:
        if isinstance(tree, Node):
            print(json.dumps(tree.toJSON()))

if __name__ == "__main__":
    main()