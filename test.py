from pathlib import Path
import json
import ast
import traceback
import subprocess
from compiler.typechecker import TypeChecker
from compiler.typeeraser import TypeEraser
from compiler.typesystem import TypeSystem
from compiler.compiler import Compiler
import llvmlite.binding as llvm
from ctypes import CFUNCTYPE
from typing import List, Optional

dump_location = True
error_flags = {"error", "Error", "Exception",
               "exception", "Expected", "expected", "failed"}


disabled_llvm_tests = []

disabled_jvm_tests = []

disabled_cil_tests = []

disabled_wasm_tests = []


def should_skip(disabled_tests: List[str], test: Path) -> bool:
    skip = False
    for disabled in disabled_tests:
        if disabled in str(test):
            skip = True
            print("Skipping " + str(test))
            break
    return skip


def run_all_tests():
    run_parse_tests()
    run_typecheck_tests()
    run_python_backend_tests()
    run_closure_tests()
    run_jvm_tests()
    run_cil_tests()
    run_wasm_tests()
    run_llvm_tests()
    # run_llvm_test("tests/runtime/nested_list.py", "debug.ll")


def run_parse_tests():
    print("Running parser tests...\n")
    total = 0
    n_passed = 0
    passed = True
    parser_tests_dir = (Path(__file__).parent / "tests/parse/").resolve()
    for test in parser_tests_dir.glob('*.py'):
        passed = run_parse_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    # typechecker tests should all successfully parse
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_parse_test(test, False)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    # runtime tests should all successfully parse
    tc_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_typecheck_test(test, False)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} parser test cases\n".format(
        n_passed, total))


def run_typecheck_tests():
    print("Running typecheck tests...\n")
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_typecheck_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    tc_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_typecheck_test(test, False)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} typechecker test cases\n".format(
        n_passed, total))


def run_closure_tests():
    print("Running closure transformation tests...\n")
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        if not test.name.startswith("bad"):
            passed = run_closure_test(test)
            total += 1
            if not passed:
                print("Failed: " + str(test))
            else:
                n_passed += 1
    tc_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_closure_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} closure transformation test cases\n".format(
        n_passed, total))
    if total == n_passed:
        subprocess.run("cd {} && rm -f *.test.py".format(
            str(Path(__file__).parent.resolve())
        ), shell=True)
    print("Running closure transformation runtime tests...\n")
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_closure_runtime_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} closure transformation runtime test cases\n".format(
        n_passed, total))
    if total == n_passed:
        subprocess.run("cd {} && rm -f *.test.py".format(
            str(Path(__file__).parent.resolve())
        ), shell=True)


def run_python_backend_tests():
    print("Running Python backend tests...\n")
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        if not test.name.startswith("bad"):
            passed = run_python_emit_test(test)
            total += 1
            if not passed:
                print("Failed: " + str(test))
            else:
                n_passed += 1
    print("\nPassed {:d} out of {:d} Python backend emit test cases\n".format(
        n_passed, total))
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_python_runtime_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test))
        else:
            n_passed += 1
    if total == n_passed:
        subprocess.run("cd {} && rm -f *.test.py".format(
            str(Path(__file__).parent.resolve())
        ), shell=True)
    else:
        print("\nNot all test cases passed. Please run `make clean` after inspecting the output")
    print("\nPassed {:d} out of {:d} Python backend runtime test cases\n".format(
        n_passed, total))


def run_wasm_tests():
    print("Running WASM backend tests...\n")
    total = 0
    n_passed = 0
    wasm_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in wasm_tests_dir.glob('*.py'):
        if should_skip(disabled_wasm_tests, test):
            continue
        passed = run_wasm_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test) + "\n")
        else:
            n_passed += 1
    if total == n_passed:
        subprocess.run("cd {} && rm -f *.wat && rm -f *.wasm".format(
            str(Path(__file__).parent.resolve())
        ), shell=True)
    else:
        print("\nNot all test cases passed. Please run `make clean` after inspecting the output")
    print("\nPassed {:d} out of {:d} WASM backend test cases\n".format(
        n_passed, total))


def run_jvm_tests():
    print("Running JVM backend tests...\n")
    total = 0
    n_passed = 0
    jvm_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in jvm_tests_dir.glob('*.py'):
        if should_skip(disabled_jvm_tests, test):
            continue
        passed = run_jvm_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test) + "\n")
        else:
            n_passed += 1
    if total == n_passed:
        subprocess.run("cd {} && rm -f *.j && rm -f *.class".format(
            str(Path(__file__).parent.resolve())
        ), shell=True)
    else:
        print("\nNot all test cases passed. Please run `make clean` after inspecting the output")
    print("\nPassed {:d} out of {:d} JVM backend test cases\n".format(
        n_passed, total))


def run_cil_tests():
    print("Running CIL backend tests...\n")
    total = 0
    n_passed = 0
    cil_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in cil_tests_dir.glob('*.py'):
        if should_skip(disabled_cil_tests, test):
            continue
        passed = run_cil_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test) + "\n")
        else:
            n_passed += 1
    if total == n_passed:
        subprocess.run("cd {} && rm -f *.cil && rm -f *.exe".format(
            str(Path(__file__).parent.resolve())
        ), shell=True)
    else:
        print("\nNot all test cases passed. Please run `make clean` after inspecting the output")
    print("\nPassed {:d} out of {:d} CIL backend test cases\n".format(
        n_passed, total))


def run_parse_test(test, bad=True) -> bool:
    # if bad=True, then test cases prefixed with bad are expected to fail
    compiler = Compiler()
    astparser = compiler.parser
    ast = compiler.parse(test)
    # check that parsing error exists
    if bad and test.name.startswith("bad"):
        return len(astparser.errors) > 0
    if len(astparser.errors) > 0:
        return False
    ast_json = ast.toJSON(True)
    try:
        with test.with_suffix(".py.ast").open("r") as f:
            correct_json = json.load(f)
            return ast_equals(ast_json, correct_json)
    except:
        with test.with_suffix(".py.ast.typed").open("r") as f:
            correct_json = json.load(f)
            return ast_equals(correct_json, ast_json)


def run_typecheck_test(test, checkAst=True) -> bool:
    try:
        compiler = Compiler()
        astparser = compiler.parser
        ast = compiler.parse(test)
        if len(astparser.errors) > 0:
            return False
        compiler.typecheck(ast)
        if checkAst:
            ast_json = ast.toJSON(True)
            with test.with_suffix(".py.ast.typed").open("r") as f:
                correct_json = json.load(f)
                match = ast_equals(ast_json, correct_json)
                return match
        else:
            if len(ast.errors.errors) > 0:
                for e in ast.errors.errors:
                    print(e.toJSON(dump_location))
                return False
            return True
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False


def run_closure_test(test) -> bool:
    # check that typechecking passes with the transformed AST
    # for valid cases only
    try:
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        compiler.closurepass(chocopy_ast)
        # clean types to get fresh typecheck
        chocopy_ast.visit(TypeEraser())
        tc = TypeChecker(TypeSystem())
        tc.visit(chocopy_ast)
        if len(chocopy_ast.errors.errors) > 0:
            for e in ast.errors.errors:
                print(e.toJSON(dump_location))
            return False
        return True
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False


def run_closure_runtime_test(test) -> bool:
    infile_name = str(test)[:-3].split("/")[-1]
    try:
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        compiler.closurepass(chocopy_ast)
        builder = compiler.emitPython(chocopy_ast)
        name = f"./{infile_name}.test.py"
        with open(name, "w") as f:
            f.write(builder.emit())
        output = subprocess.check_output(
            f"cd {str(Path(__file__).parent.resolve())} && python3 {name}",
            shell=True)
        lines = output.decode().split("\n")
        passed = True
        for l in lines:
            for e in error_flags:
                if e in l:
                    passed = False
                    print(l)
                    break
        return passed
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False


def run_python_emit_test(test) -> bool:
    try:
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        builder = compiler.emitPython(chocopy_ast)
        ast.parse(builder.emit())
        return True
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False


def run_python_runtime_test(test) -> bool:
    infile_name = str(test)[:-3].split("/")[-1]
    try:
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        builder = compiler.emitPython(chocopy_ast)
        name = f"./{infile_name}.test.py"
        with open(name, "w") as f:
            f.write(builder.emit())
        output = subprocess.check_output(
            f"cd {str(Path(__file__).parent.resolve())} && python3 {name}",
            shell=True)
        lines = output.decode().split("\n")
        passed = True
        for l in lines:
            for e in error_flags:
                if e in l:
                    passed = False
                    print(l)
                    break
        return passed
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False


def run_jvm_test(test) -> bool:
    passed = True
    try:
        infile_name = str(test)[:-3].split("/")[-1]
        outdir = "./"
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        jvm_emitters = compiler.emitJVM(infile_name, chocopy_ast)
        for cls in jvm_emitters:
            jvm_emitter = jvm_emitters[cls]
            fname = outdir + cls + ".j"
            with open(fname, "w") as f:
                f.write(jvm_emitter.emit())
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False
    try:
        assembler_commands = [
            "python3 ../Krakatau/assemble.py -q ./{}.j".format(cls) for cls in jvm_emitters]
        output = subprocess.check_output("cd {} && {} && java -cp . {}".format(
            str(Path(__file__).parent.resolve()),
            " && ".join(assembler_commands),
            str(test.name[:-3])
        ), shell=True)
        lines = output.decode().split("\n")
        for l in lines:
            for e in error_flags:
                if e in l:
                    passed = False
                    print(l)
                    break
    except Exception as e:
        print(e)
        return False
    return passed


def run_cil_test(test) -> bool:
    passed = True
    name = str(test.name[:-3])
    try:
        infile_name = name.split("/")[-1]
        outdir = "./"
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        cil_emitter = compiler.emitCIL(infile_name, chocopy_ast)
        fname = outdir + cil_emitter.name + ".cil"
        with open(fname, "w") as f:
            f.write(cil_emitter.emit())
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False
    try:
        assembler_commands = [f"ilasm {name}.cil"]
        output = subprocess.check_output("cd {} && {} && mono {}.exe".format(
            str(Path(__file__).parent.resolve()),
            " && ".join(assembler_commands),
            name
        ), shell=True)
        lines = output.decode().split("\n")
        for l in lines:
            for e in error_flags:
                if e in l:
                    passed = False
                    print(l)
                    break
    except Exception as e:
        print(e)
        return False
    return passed


def run_wasm_test(test) -> bool:
    passed = True
    name = str(test.name[:-3])
    try:
        infile_name = name.split("/")[-1]
        outdir = "./"
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        wasm_emitter = compiler.emitWASM(infile_name, chocopy_ast)
        fname = outdir + name + ".wat"
        with open(fname, "w") as f:
            f.write(wasm_emitter.emit())
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False
    try:
        output = subprocess.check_output(
            f"wat2wasm {name}.wat -o {name}.wasm && node wasm.js {name}.wasm", shell=True)
        lines = output.decode().split("\n")
        for l in lines:
            for e in error_flags:
                if e in l:
                    passed = False
                    print(l)
                    break
    except Exception as e:
        print(e)
        return False
    return passed


def ast_equals(d1, d2) -> bool:
    # precondition: the input dict must represent a well-formed AST
    # d1 is the correct AST, d2 is the AST output by this compiler
    if isinstance(d1, dict) and isinstance(d2, dict):
        for k, v in d1.items():
            if k not in d2 and k != "inferredType":
                print("Expected field: " + k)
                return False
            # only check starting line of node
            if k == "location":
                if d1[k][0] != d2[k][0]:
                    print("Expected starting line {:d}, got {:d}".format(
                        d1[k][0], d2[k][0]))
                    return False
            # check number of errors, not the messages
            elif k == "errors":
                if len(d1[k]["errors"]) != len(d2[k]["errors"]):
                    print("Expected {:d} errors, got {:d}".format(
                        len(d1[k]["errors"]), len(d2[k]["errors"])))
                    return False
            elif k == "errorMsg":
                pass  # only check presence of message, not content
            elif k == "inferredType":
                if k in d2 and not ast_equals(v, d2[k]):
                    return False
            elif not ast_equals(v, d2[k]):
                return False
        for k in d2.keys():
            if k not in d1 and k != "inferredType":
                print("Unxpected field: " + k)
                return False
        return True
    if isinstance(d1, list) and isinstance(d2, list):
        if len(d1) != len(d2):
            print("Expected list of length {:s}, got {:s}".format(
                len(d1), len(d2)))
            return False
        for i in range(len(d1)):
            if not ast_equals(d1[i], d2[i]):
                return False
        return True
    if d1 != d2:
        print("Expected {:s}, got {:s}".format(str(d1), str(d2)))
    return d1 == d2


def run_llvm_tests():
    print("Running LLVM backend tests...\n")
    total = 0
    n_passed = 0
    llvm_tests_dir = (Path(__file__).parent / "tests/runtime/").resolve()
    for test in llvm_tests_dir.glob('*.py'):
        skip = False
        for disabled in disabled_llvm_tests:
            if disabled in str(test):
                skip = True
                break
        if skip:
            print("Skipping: " + str(test) + "\n")
            continue
        passed = run_llvm_test(test)
        total += 1
        if not passed:
            print("Failed: " + str(test) + "\n")
        else:
            print("Passed: " + str(test) + "\n")
            n_passed += 1
    if total != n_passed:
        print("\nNot all test cases passed")
    print("\nPassed {:d} out of {:d} LLVM backend test cases\n".format(
        n_passed, total))


def eval_llvm(module):
    # eval the compiled LLVMLite from Python
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    llvmmod = llvm.parse_assembly(str(module))
    llvmmod.verify()
    with llvm.create_mcjit_compiler(llvmmod, target_machine) as ee:
        ee.finalize_object()
        fptr = CFUNCTYPE(None)(ee.get_function_address("main"))
        fptr()


def run_llvm_test(test: str, debug: Optional[str] = None):
    if debug:
        print("Running test", test)
    try:
        compiler = Compiler()
        chocopy_ast = build_and_check_ast(compiler, test)
        module = compiler.emitLLVM(chocopy_ast)
        if debug:
            with open(debug, "w") as f:
                f.write(str(module))
        eval_llvm(module)
        return True
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False


def build_and_check_ast(compiler: Compiler, test: str):
    astparser = compiler.parser
    chocopy_ast = compiler.parse(test)
    if len(astparser.errors) > 0:
        print(astparser.errors)
        assert len(astparser.errors) == 0
    compiler.typecheck(chocopy_ast)
    if len(compiler.typechecker.errors) > 0:
        print(compiler.typechecker.errors)
        assert len(compiler.typechecker.errors) == 0
    return chocopy_ast
