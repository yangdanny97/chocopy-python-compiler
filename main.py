import argparse
import json
from test import run_all_tests, run_parse_tests, run_typecheck_tests
from compiler.compiler import Compiler
from compiler.builder import Builder
from compiler.astnodes import Node
from compiler.jvm_backend import JvmBackend

mode_help = (
    'Modes:\n' +
    'parse - output AST as JSON\n' +
    'tc - output typechecked AST as JSON\n' +
    'python - output untyped Python 3 source code' + 
    'jvm - output JVM bytecode as text formatted for the Krakatau assembler'
)

def out_msg(path):
    print("Output to {}".format(path))

def main():
    parser = argparse.ArgumentParser(description='Chocopy frontend')
    parser.add_argument('--mode', dest='mode', choices=["parse", "tc", "python", "jvm"], default="python",
                        help=mode_help)
    parser.add_argument('--print', dest='should_print', action='store_true',
                        help="output to stdout instead of file")
    parser.add_argument('--test', dest='test', action='store_true',
                        help="run all test cases")
    parser.add_argument('infile', nargs='?', type=str, default=None)
    parser.add_argument('outfile', nargs='?', type=str, default=None)
    args = parser.parse_args()

    if args.test:
        run_all_tests()
        return

    infile = args.infile
    outfile = args.outfile
    if args.infile == None:
        print("Error: must specify input file")
        parser.print_help()
        return

    if args.infile[-3:] != ".py":
        print("Error: input file must end with .py")
        return

    infile_name = infile[:-3].split("/")[-1]
    infile_no_extension = infile[:-3]

    if args.outfile is None:
        if args.mode == "tc":
            outfile = infile + ".ast.typed"
        elif args.mode == "parse":
            outfile = infile + ".ast"
        elif args.mode == "python":
            outfile = infile_no_extension + ".out.py"
        elif args.mode == "jvm":
            outfile = infile_no_extension + ".j"

    compiler = Compiler()
    astparser = compiler.parser
    tc = compiler.typechecker
    tree = compiler.parse(infile)

    if len(astparser.errors) > 0 or not isinstance(tree, Node):
        print("Encountered parse errors. Exiting.")
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
        ast_json = tree.toJSON(False)
        if args.should_print: 
            print(json.dumps(ast_json, indent=2))
        else:
            with open(outfile, "w") as f:
                out_msg(outfile)
                json.dump(ast_json, f, indent=2)
    elif args.mode == "python":
        builder = Builder()
        tree.getPythonStr(builder)
        if args.should_print:
            print(builder.emit())
        else: 
            with open(outfile, "w") as f:
                out_msg(outfile)
                f.write(builder.emit())
    elif args.mode == "jvm":
        jvm_emitter = JvmBackend(infile_name)
        jvm_emitter.visit(tree)
        if args.should_print:
            print(jvm_emitter.emit())
        else: 
            with open(outfile, "w") as f:
                out_msg(outfile)
                f.write(jvm_emitter.emit())       

if __name__ == "__main__":
    main()
