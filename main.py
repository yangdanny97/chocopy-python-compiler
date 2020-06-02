import argparse
import json
from test import run_all_tests, run_parse_tests, run_typecheck_tests
from compiler.compiler import Compiler
from compiler.parser import Parser
from compiler.typechecker import TypeChecker
from compiler.astnodes import Node


def main():
    parser = argparse.ArgumentParser(description='Chocopy frontend')
    parser.add_argument('-m', '--mode', dest='mode', choices=["parse", "tc", "llvm"], default="tc",
                        help='modes:\nparse (output AST before typechecking)\ntc (output typechecked AST)\nllvm (output LLVM IR)')
    parser.add_argument('-o', '--output', dest='output', action='store_false',
                        help="output to stdout instead of file")
    parser.add_argument('--test-all', dest='testall', action='store_true',
                        help="run all test cases")
    parser.add_argument('--test-parse', dest='testparse', action='store_true',
                        help="run parser test cases")
    parser.add_argument('--test-tc', dest='testtc', action='store_true',
                        help="run typechecker test cases")
    parser.add_argument('infile', nargs='?', type=str, default=None)
    parser.add_argument('outfile', nargs='?', type=str, default=None)
    args = parser.parse_args()

    if args.testall:
        run_all_tests()
        return

    if args.testparse:
        run_parse_tests()
        return

    if args.testtc:
        run_typecheck_tests()
        return

    infile = args.infile
    outfile = args.outfile
    if args.infile == None:
        print("Error: must specify input file")
        parser.print_help()
        return

    if args.outfile is None:
        if args.mode == "tc":
            outfile = infile + ".ast.typed"
        elif args.mode == "parse":
            outfile = infile + ".ast"
        elif args.mode == "llvm":
            outfile = infile + ".ll"

    compiler = Compiler()
    astparser = compiler.parser
    tc = compiler.typechecker
    tree = compiler.parse(infile)

    if len(astparser.errors) > 0:
        for e in astparser.errors:
            print(e)
            return
    elif args.mode != "parse":
        compiler.typecheck(tree)
        if len(tc.errors) > 0:
            for e in astparser.errors:
                print(e)
                return

    if args.mode in {"parse", "tc"}:
        ast_json = tree.toJSON()
        if args.output:  # output to file
            with open(outfile, "w") as f:
                json.dump(ast_json, f)
        else:  # output to stdout
            if isinstance(tree, Node):
                print(json.dumps(ast_json))
    elif args.mode == "llvm":
        pass  # TODO


if __name__ == "__main__":
    main()
