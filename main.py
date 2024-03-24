import argparse
import json
from test import run_all_tests
from compiler.compiler import Compiler
from compiler.astnodes import Node

mode_help = (
    'Modes:\n' +
    'parse - output AST in JSON format\n' +
    'tc - output typechecked AST in JSON format\n' +
    'python - output untyped Python 3 source code\n' +
    'hoist - output untyped Python 3 source code w/o nonlocals or nested function definitions\n' +
    'jvm - output JVM bytecode formatted for the Krakatau assembler\n' +
    'cil - output CIL bytecode formatted for the Mono ilasm assembler\n' +
    'wasm - output WASM in WAT format\n' +
    'llvm - output LLVM IR\n'
)


def out_msg(path, verbose):
    if verbose:
        print("Output to {}".format(path))


def main():
    parser = argparse.ArgumentParser(description='Chocopy frontend')
    parser.add_argument('--mode',
                        dest='mode',
                        choices=["parse", "tc", "python", "jvm",
                                 "hoist", "cil", "wasm", "llvm"],
                        default="python",
                        help=mode_help)
    parser.add_argument('--print', dest='should_print', action='store_true',
                        help="output to stdout instead of file")
    parser.add_argument('--test', dest='test', action='store_true',
                        help="run all test cases")
    parser.add_argument('--verbose', dest='verbose', action='store_true',
                        help="verbose output")
    parser.add_argument('infile', nargs='?', type=str, default=None)
    parser.add_argument('outdir', nargs='?', type=str, default=None)
    args = parser.parse_args()

    if args.test:
        run_all_tests()
        return

    infile = args.infile
    outdir = args.outdir
    if args.infile is None:
        parser.print_help()
        raise Exception("Error: must specify input file")

    if args.infile[-3:] != ".py":
        raise Exception("Error: input file must end with .py")

    infile_name = infile[:-3].split("/")[-1]

    if outdir is None:
        outdir = "./"
    elif outdir[-1] != "/":
        outdir = outdir + "/"

    outfile = None
    if args.mode == "tc":
        outfile = outdir + infile_name + ".ast.typed"
    elif args.mode == "parse":
        outfile = outdir + infile_name + ".ast"
    elif args.mode in {"python", "hoist"}:
        outfile = outdir + infile_name + ".out.py"
    elif args.mode == "jvm":
        outfile = outdir + infile_name + ".j"
    elif args.mode == "llvm":
        outfile = outdir + infile_name + ".ll"
    elif args.mode == "cil":
        outfile = outdir + infile_name + ".cil"
    elif args.mode == "wasm":
        outfile = outdir + infile_name + ".wat"
    assert outfile is not None

    compiler = Compiler()
    astparser = compiler.parser
    tc = compiler.typechecker
    tree = compiler.parse(infile)

    if len(astparser.errors) > 0 or not isinstance(tree, Node):
        for e in astparser.errors:
            print(e)
        raise Exception("Encountered parse errors. Exiting.")
    elif args.mode != "parse":
        compiler.typecheck(tree)
        if len(tc.errors) > 0:
            for e in tc.errors:
                print(e)
            raise Exception("Encountered typecheck errors. Exiting.")

    if args.mode in {"parse", "tc"}:
        ast_json = tree.toJSON(False)
        if args.should_print:
            print(json.dumps(ast_json, indent=2))
        else:
            with open(outfile, "w") as f:
                out_msg(outfile, args.verbose)
                json.dump(ast_json, f, indent=2)
    elif args.mode == "python":
        builder = compiler.emitPython(tree)
        if args.should_print:
            print(builder.emit())
        else:
            with open(outfile, "w") as f:
                out_msg(outfile, args.verbose)
                f.write(builder.emit())
    elif args.mode == "hoist":
        compiler.closurepass(tree)
        builder = compiler.emitPython(tree)
        if args.should_print:
            print(builder.emit())
        else:
            with open(outfile, "w") as f:
                out_msg(outfile, args.verbose)
                f.write(builder.emit())
    elif args.mode == "jvm":
        jvm_emitters = compiler.emitJVM(infile_name, tree)
        for cls in jvm_emitters:
            jvm_emitter = jvm_emitters[cls]
            if args.should_print:
                print(jvm_emitter.emit())
            else:
                fname = outdir + cls + ".j"
                with open(fname, "w") as f:
                    out_msg(fname, args.verbose)
                    f.write(jvm_emitter.emit())
    elif args.mode == "cil":
        cil_emitter = compiler.emitCIL(infile_name, tree)
        if args.should_print:
            print(cil_emitter.emit())
        else:
            with open(outfile, "w") as f:
                out_msg(outfile, args.verbose)
                f.write(cil_emitter.emit())
    elif args.mode == "wasm":
        wat_emitter = compiler.emitWASM(infile_name, tree)
        if args.should_print:
            print(wat_emitter.emit())
        else:
            with open(outfile, "w") as f:
                out_msg(outfile, args.verbose)
                f.write(wat_emitter.emit())
    elif args.mode == "llvm":
        llvm_module = compiler.emitLLVM(tree)
        if args.should_print:
            print(str(llvm_module))
        else:
            with open(outfile, "w") as f:
                out_msg(outfile, args.verbose)
                f.write(str(llvm_module))


if __name__ == "__main__":
    main()
