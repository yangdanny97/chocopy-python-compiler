# chocopy-python-compiler

An ahead-of-time compiler for Chocopy, written entirely in Python. [Chocopy](https://chocopy.org/) is a subset of Python 3.6 that is used as a teaching language for Berkeley's compilers course, and has a reference implementation targeting RISC-V written in Java. It includes a relatively large set of features from Python, such as: lists, classes, methods, nested functions, and nonlocals.

This project is mostly a tool for me to learn/practice compiler writing, and I plan to extend it with additional backends if/when I have time. I hope that this project will also become a useful educational reference for other people. 

Progress is documented on my [blog](https://yangdanny97.github.io/blog/):
- [Part 1: Frontend/Typechecker](https://yangdanny97.github.io/blog/2020/05/29/chocopy-typechecker)
- [Part 2: JVM backend](https://yangdanny97.github.io/blog/2021/08/26/chocopy-jvm-backend)

This compiler's frontend matches the functionality of the first 2 passes (parsing & typechecking) Chocopy's reference compiler implementation, and outputs the AST in a JSON format that is compatible with the reference implementation. That means that you can parse and typecheck the Chocopy file with this compiler, then use the reference implementation's backend to handle assembly code generation.

This compiler currently supports 2 backends, which are not found in the reference implementation: 
- Untyped Python 3 source code
- JVM bytecode, formatted for the Krakatau assembler

## Requires:
- Python 3.6 - 3.8
- [Krakatau assembler](https://github.com/Storyyeller/Krakatau) (only if you want to use the JVM backend)

## Usage

Invoke `main.py` with the appropriate flags, plus the input file (required) and output file (optional). 

The input file should have extension `.py`. If the output file is not provided, then outputs will depend on the input file name:
- AST JSON outputs will be written to a file of the same name/location as the input file, with extension `.py.ast`
- Python source outputs will be written to a file of the same name/location as the input file, with extension `.out.py`
- JVM outputs will be written to the same location as the input file, with the extension `.j`

**Flags:**

- `-h` - show help
- `-t` - do not typecheck the AST
- `-o` - do not output the AST as a JSON file (instead, print the output to stdout)
- `--test` - run entire test suite
-  `--mode` - choose from the following modes:
    - `parse` - output AST in JSON format
    - `tc` - output typechecked AST in JSON format
    - `python` - output untyped Python 3 source code
    - `hoist` - output untyped Python 3 source code w/o nonlocals or nested function definitions
    - `jvm` - output JVM bytecode formatted for the Krakatau assembler

## Differences from the reference implementation:

The reference implementation represents a node's location as a four item list of \[start line, start col, end line, end col]. Since this implementation uses Python's built-in parser, only the starting position of each node is valid. Furthermore, the starting columns of nodes may differ slightly from the reference implementation. This compiler still outputs each node's location as a four item list for compatibility reasons, but only the starting line number for each node is guaranteed to match the reference implementation.

The exact error messages from typechecking do not necessarily match the reference implementation, but the total number of messages (and the nodes that the messages are attached to) will match.

This compiler support an extra standard function, `__assert__`, which takes in a single `bool` argument and functions exactly like Python's `assert` statement. It is used in the test suite to assert values in runtime tests.

## JVM Backend Notes:

The JVM backend for this compiler outputs JVM bytecode in plaintext formatted for the Krakatau assembler. Here's how you can compile and run a file using this backend:
1. Use this compiler to generate plaintext bytecode 
    - Format:  `python3 main.py --mode jvm <input file> <output dir>`
    - Example: `python3 main.py --mode jvm tests/runtime/binary_tree.py .`
2. Run the Krakatau assembler to generate `.class` files - note that this must be done for EACH .j file generated by the compiler
    - Format:  `python3 <path to Krakatau/Assemble.py> -q <.j file>`
    - Example: `ls *.j | xargs -L1 python3 ../Krakatau/assemble.py -q`
3. Run the `.class` files
    - Example: `java -cp <output dir> <input file name with no extensions>`
    - Example: `java -cp . binary_tree`

The `compile_jvm.sh` script is a useful utility to compile and run files with the JVM backend with a single command (provide the path to the input source file as an argument). 
- To run the same example as above, run `./compile_jvm.sh tests/runtime/binary_tree.py`

Note that in the above example commands & the `compile_jvm.sh` script all expect the Krakatau directory and this repository's directory to share the same parent - commands will differ if you cloned Krakatau to a different location.

### JVM Backend - Known Issues:
- Since bytecode for each class is stored in a separate file, on operating systems with case-insensitive file names (like MacOS) you cannot have 2 classes whose names only differ by case.
- Since the main JVM class for a Chocopy program shares the name of the file, do not define classes with the same name as the source file.
- The special parameter `self` in methods and constructors may not be referenced by a `nonlocal` declaration. The Java equivalent, `this`, is final and cannot be assigned to.
- Some large programs may cause the JVM to run out of stack space, since each frame currently has a maximum stack size of 500.

## Test Suite

Most of the test cases are taken from test suites included in the release code for CS164, with some additional tests written for more coverage. Tests include both static validation of generated/annotated ASTs, as well as runtime tests that check the correctness of output code.
