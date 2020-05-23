# chocopy-python-frontend

A compiler frontend/typechecker for Chocopy, built in Python. [Chocopy](https://chocopy.org/) is a subset of Python 3.6 that is used for Berkeley's compilers course. 

This compiler frontend has the same functionality as the first 2 passes (parsing & typechecking) Chocopy's reference compiler implementation, and outputs the AST in a JSON format that is compatible with the reference implementation. 

That means that you can parse and typecheck the Chocopy file with this compiler, then use the reference implementation's backend to handle the assembly code generation.

The implementation uses Python's `ast` module, and is designed to work with Python 3.6 - 3.8

Most of the test cases are taken from test suites included in the PA1 and PA2 release code for CS164, with some additional tests written for more complete coverage.

## Usage

Invoke `main.py` with the appropriate flags, plus the input file (required) and output file (optional). 

The input file should have extension `.py`. If the output file is not provided, then the AST JSON will be dumped to a file of the same name/location as the input file, with extension `.py.ast`.

**Flags:**

- `-h` - show help
- `-t` - do not typecheck the AST
- `-o` - do not output the AST as a JSON
- `--test-all` - run entire test suite
- `--test-parse` - run parsing tests
- `--test-tc` - run typechecking tests

## Differences from the reference implementation:

The reference implementation represents a node's location as a four item list of \[start line, start col, end line, end col]. Python's parser does not always provide the end line/end column of a node, and the starting column sometimes differs from the reference implementation's parser (a handful of edge cases which do not impact the usefulness of error messages). Although this compiler still outputs each node's location as a four item list for compatibility reasons, only the starting line number for the node is guaranteed to match the reference implementation.

The exact error messages from typechecking do not necessarily match the reference implementation, but the total number of messages and nodes that the messages are attached to will match.

