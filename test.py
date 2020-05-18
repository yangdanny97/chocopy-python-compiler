from pathlib import Path
import compiler.chocopy
import json

def run_all_tests():
    run_parse_tests()
    run_typecheck_tests()

def run_parse_tests():
    print("Running parser tests...")
    print("")
    total = 0
    passed = 0
    parser_tests_dir = (Path(__file__).parent / "tests/parse/").resolve()
    for test in parser_tests_dir.glob('*.py'):
        passed = run_parse_test(test)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            passed += 1
    print("")
    print("Passed {:d} out of {:d} cases".format(passed, total))
    print("")

def run_typecheck_tests():
    print("Running typecheck tests...")
    print("")
    total = 0
    passed = 0
    tc_tests_dir = (Path(__file__).parent / "tests/typecheck/").resolve()
    for test in tc_tests_dir.glob('*.py'):
        passed = run_typecheck_test(test)
        total += 1
        if not passed:
            print("Failed: " + test.name)
        else:
            passed += 1
    print("")
    print("Passed {:d} out of {:d} cases".format(passed, total))
    print("")

def run_parse_test(test):
    passed = True
    ast = chocopy.parse(test)
    ast_json = ast.toJSON()
    with test.with_suffix(".py.ast").open("r") as f:
        correct_json = json.load(f)
        passed = dict_equals(ast_json, correct_json)
    return passed

def run_typecheck_test(test):
    passed = True
    ast = chocopy.parse(test)
    ast = chocopy.typecheck(ast)
    ast_json = ast.toJSON()
    with test.with_suffix(".py.ast.typed").open("r") as f:
        correct_json = json.load(f)
        passed = dict_equals(ast_json, correct_json)
    return passed

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
