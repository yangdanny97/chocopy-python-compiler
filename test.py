from pathlib import Path
from compiler.compiler import Compiler
from compiler.builder import Builder
import json
import ast
from compiler.typechecker import TypeChecker
from compiler.typeeraser import TypeEraser
from compiler.typesystem import TypeSystem
from compiler.jvm_backend import JvmBackend
import traceback
import subprocess

dump_location = True

def run_all_tests():
    run_parse_tests()
    run_typecheck_tests()
    run_closure_tests()
    run_python_emit_tests()
    run_jvm_tests()

def run_parse_tests():
    print("Running parser tests...\n")
    total = 0
    n_passed = 0
    passed = True
    print("Running tests in: tests/parse/")
    parser_tests_dir = (Path(__file__).parent / "tests/parse/").resolve()
    for test in parser_tests_dir.glob('*.py'):
        passed = run_parse_test(test)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            n_passed += 1
    print("Running tests in: tests/typecheck/")
    # typechecker tests should all successfully parse
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_parse_test(test, False)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} parser test cases\n".format(n_passed, total))

def run_typecheck_tests():
    print("Running typecheck tests...\n")
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_typecheck_test(test)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} typechecker test cases\n".format(n_passed, total))

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
                print("Failed: " + test.name)
            else:
                n_passed += 1
    print("\nPassed {:d} out of {:d} closure transformation test cases\n".format(n_passed, total))

def run_python_emit_tests():
    print("Running Python backend tests...\n")
    total = 0
    n_passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_python_emit_test(test)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            n_passed += 1
    print("\nPassed {:d} out of {:d} Python backend test cases\n".format(n_passed, total))

def run_jvm_tests():
    print("Running JVM backend tests...\n")
    total = 0
    n_passed = 0
    jvm_tests_dir = (Path(__file__).parent / "tests/jvm/").resolve()
    for test in jvm_tests_dir.glob('*.py'):
        passed = run_jvm_test(test)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            n_passed += 1
    subprocess.run("cd {} && rm *.j && rm *.class".format(
        str(Path(__file__).parent.resolve())
    ), shell=True)
    print("\nPassed {:d} out of {:d} JVM backend test cases\n".format(n_passed, total))

def run_parse_test(test, bad=True)->bool:
    # if bad=True, then test cases prefixed with bad are expected to fail
    compiler = Compiler()
    astparser = compiler.parser
    ast = compiler.parse(test)
    # check that parsing error exists
    if bad and test.name.startswith("bad"):
        return len(astparser.errors) > 0
    if len(astparser.errors) > 0:
        return False
    ast_json = ast.toJSON(dump_location)
    try:
        with test.with_suffix(".py.ast").open("r") as f:
            correct_json = json.load(f)
            return ast_equals(ast_json, correct_json)
    except:
        with test.with_suffix(".py.ast.typed").open("r") as f:
            correct_json = json.load(f)
            return ast_equals(ast_json, correct_json)

def run_typecheck_test(test)->bool:
    try:
        compiler = Compiler()
        astparser = compiler.parser
        ast = compiler.parse(test)
        if len(astparser.errors) > 0:
            return False
        compiler.typecheck(ast)
        ast_json = ast.toJSON(dump_location)
        with test.with_suffix(".py.ast.typed").open("r") as f:
            correct_json = json.load(f)
            return ast_equals(ast_json, correct_json)
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False

def run_closure_test(test)->bool:
    # check that typechecking passes with the transformed AST
    # for valid cases only
    try:
        compiler = Compiler()
        astparser = compiler.parser
        ast = compiler.parse(test)
        if len(astparser.errors) > 0:
            return False
        tc = compiler.typechecker
        compiler.typecheck(ast)
        compiler.closurepass(ast)
        # clean types to get fresh typecheck
        ast.visit(TypeEraser())
        tc = TypeChecker(TypeSystem())
        tc.visit(ast)
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

def run_python_emit_test(test)->bool:
    builder = Builder()
    try:
        compiler = Compiler()
        astparser = compiler.parser
        chocopy_ast = compiler.parse(test)
        if len(astparser.errors) > 0:
            return False
        compiler.typecheck(chocopy_ast)
        chocopy_ast.getPythonStr(builder)
        ast.parse(builder.emit())
        return True
    except Exception as e:
        print("Internal compiler error:", test)
        track = traceback.format_exc()
        print(e)
        print(track)
        return False

def run_jvm_test(test)->bool:
    passed = True
    output  = subprocess.check_output("cd {} && ./compile_jvm.sh tests/jvm/{}".format(
        str(Path(__file__).parent.resolve()),
        str(test.name)
    ), shell=True)
    lines = output.decode().split("\n")
    error_flags = {"error", "Error", "Exception", "exception"}
    for l in lines:
        for e in error_flags:
            if e in l:
                passed = False
                print(l)
                break
    return passed

def ast_equals(d1, d2)->bool:
    # precondition: the input dict must represent a well-formed AST
    if isinstance(d1, dict) and isinstance(d2, dict):
        for k, v in d1.items():
            if k not in d2 and k != "inferredType":
                return False
            # only check starting line of node
            if k == "location":
                if d1[k][0] != d2[k][0]:
                    return False
            # check number of errors, not the messages
            elif k == "errors":
                if len(d1[k]["errors"]) != len(d2[k]["errors"]):
                    return False
            elif k == "errorMsg":
                pass # only check presence of message, not content
            elif k == "inferredType":
                if k in d2 and not ast_equals(v, d2[k]):
                    return False
            elif not ast_equals(v, d2[k]):
                return False
        for k in d2.keys():
            if k not in d1 and k != "inferredType":
                return False
        return True
    if isinstance(d1, list) and isinstance(d2, list):
        if len(d1) != len(d2):
            return False
        for i in range(len(d1)):
            if not ast_equals(d1[i], d2[i]):
                return False
        return True
    return d1 == d2
