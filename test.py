from pathlib import Path
import compiler.chocopy
import json
from compiler.parser import Parser
from compiler.typechecker import TypeChecker

def run_all_tests():
    run_parse_tests()
    run_typecheck_tests()

def run_parse_tests():
    print("Running parser tests...")
    print("")
    total = 0
    n_passed = 0
    passed = True
    parser_tests_dir = (Path(__file__).parent / "tests/parse/").resolve()
    for test in parser_tests_dir.glob('*.py'):
        try:
            passed = run_parse_test(test)
        except:
            passed = False
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            n_passed += 1
    print("")
    print("Passed {:d} out of {:d} cases".format(n_passed, total))
    print("")

def run_typecheck_tests():
    print("Running typecheck tests...")
    print("")
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
    print("")
    print("Passed {:d} out of {:d} cases".format(n_passed, total))
    print("")

def run_parse_test(test):
    parser = Parser()
    ast = chocopy.parse(test, parser)
    if len(parser.errors) > 0:
        return False
    ast_json = ast.toJSON()
    with test.with_suffix(".py.ast").open("r") as f:
        correct_json = json.load(f)
        return dict_equals(ast_json, correct_json)

def run_typecheck_test(test):
    ast = chocopy.parse(test)
    tc = TypeChecker()
    ast = chocopy.typecheck(ast, tc)
    if len(tc.errors) > 0:
        return False
    ast_json = ast.toJSON()
    with test.with_suffix(".py.ast.typed").open("r") as f:
        correct_json = json.load(f)
        return dict_equals(ast_json, correct_json)

def dict_equals(d1, d2):
    if isinstance(d1, dict) and isinstance(d2, dict):
        for k, v in d1.items():
            if k not in d2:
                return False
            if not dict_equals(v, d2[k]):
                return False
        for k in d2.keys():
            if k not in d1:
                return False
        return True
    if isinstance(d1, list) and isinstance(d2, list):
        if len(d1) != len(d2):
            return False
        for i in range(len(d1)):
            if not dict_equals(d1[i], d2[i]):
                return False
        return True
    return d1 == d2
