# chocopy-python-frontend

A compiler frontend/typechecker for Chocopy, built entirely in Python. [Chocopy](https://chocopy.org/) is a subset of Python 3.6 that is used for Berkeley's compilers course, and has a reference compiler built in Java.

This compiler frontend has the same functionality as the first 2 passes (parsing & typechecking) Chocopy's reference compiler implementation, and outputs the AST in a JSON format that is compatible with the reference implementation. 

That means that you can parse and typecheck the Chocopy file with this compiler, then use the reference implementation's backend to handle assembly code generation.

Most of the test cases are taken from test suites included in the release code for CS164, with some additional tests written for more coverage.

## Requires:
- Python 3.6 - 3.8
- llvmlite
- LLVM

## Usage

Invoke `main.py` with the appropriate flags, plus the input file (required) and output file (optional). 

The input file should have extension `.py`. If the output file is not provided, then the AST JSON will be dumped to a file of the same name/location as the input file, with extension `.py.ast`.

**Flags:**

- `-h` - show help
- `-t` - do not typecheck the AST
- `-o` - do not output the AST as a JSON file (instead, print the output to stdout)
- `--test-all` - run entire test suite
- `--test-parse` - run parsing tests
- `--test-tc` - run typechecking tests

## Differences from the reference implementation:

The reference implementation represents a node's location as a four item list of \[start line, start col, end line, end col]. Since this implementation uses Python's built-in parser, only the starting position of each node is valid. Furthermore, the starting columns of nodes may differ slightly from the reference implementation. This compiler still outputs each node's location as a four item list for compatibility reasons, but only the starting line number for each node is guaranteed to match the reference implementation.

The exact error messages from typechecking do not necessarily match the reference implementation, but the total number of messages (and the nodes that the messages are attached to) will match.

