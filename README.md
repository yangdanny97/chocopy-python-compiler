# chocopy-python-compiler

Ahead-of-time compiler for [Chocopy](https://chocopy.org/), a subset of Python 3.6 with type annotations static type checking. 

Chocopy is used in compiler courses at several universities. This project has no relation to those courses, and is purely for my own learning/practice/fun. 

Progress is documented on my [blog](https://yangdanny97.github.io/blog/):
- [Part 1: Frontend/Typechecker](https://yangdanny97.github.io/blog/2020/05/29/chocopy-typechecker)
- [Part 2: JVM backend](https://yangdanny97.github.io/blog/2021/08/26/chocopy-jvm-backend)
- [Part 3: CIL backend](https://yangdanny97.github.io/blog/2022/05/22/chocopy-cil-backend)

## Features

This compiler is written entirely in Python. Since Chocopy is itself a subset of Python, lexing and parsing can be entirely handled by Python's `ast` module.

This compiler matches the functionality of the first 2 passes (parsing & typechecking) Chocopy's reference compiler implementation, and outputs the AST in a JSON format that is compatible with the reference implementation's backend. That means that you can parse and typecheck the Chocopy file with this compiler, then use the reference implementation's backend to handle assembly code generation.

Additionally, this compiler contains 2 backends not found in the reference implementation: 
- Untyped Python 3 source code
- JVM bytecode, formatted for the Krakatau assembler
- CIL bytecode, formatted for the Mono ilasm assembler

The test suite includes both static validation of generated/annotated ASTs, as well as runtime tests that actually execute the output programs to check correctness. Many of the AST validation test cases are taken from test suites included in the release code for Berkeley's CS164, with some additional tests written for more coverage.

## Requirements:
- Python 3.6 - 3.8
- JVM Backend Requirements:
  - [Krakatau JVM Assembler](https://github.com/Storyyeller/Krakatau)
  - Tested with Java 8
- CIL Backend Requirements:
  - [Mono](https://www.mono-project.com/)
  - Tested with Mono 6.12
- WASM Backend Requirements:
  - [WebAssembly Binary Toolkit (wabt)](https://github.com/WebAssembly/wabt), specifically the `wat2wasm` tool

## Usage

Invoke `main.py` with the appropriate flags, plus the input file (required) and output file (optional). 

The input file should have extension `.py`. If the output file is not provided, then outputs will depend on the input file name:
- AST JSON outputs will be written to a file of the same name/location as the input file, with extension `.py.ast`
- Python source outputs will be written to a file of the same name/location as the input file, with extension `.out.py`
- JVM outputs will be written to the same location as the input file, with the extension `.j`
- CIL outputs will be written to the same location as the input file, with the extension `.cil`

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
    - `cil` - output CIL bytecode formatted for the Mono ilasm assembler
    - `wasm` - output WASM as plaintext in WAT format (WIP)

## Differences from the reference implementation:

The reference implementation represents a node's location as a four item list of \[start line, start col, end line, end col]. Since this implementation uses Python's built-in parser, only the starting position of each node is valid. Furthermore, the starting columns of nodes may differ slightly from the reference implementation. This compiler still outputs each node's location as a four item list for compatibility reasons, but only the starting line number for each node is guaranteed to match the reference implementation.

The exact error messages from typechecking do not necessarily match the reference implementation, but the total number of messages (and the nodes that the messages are attached to) will match.

This compiler supports a limited version of Python's `assert` keyword. The `assert` may be followed by a single `bool` expression, which will raise an exception with an unspecified/generic message if the value is false. It is used in the test suite to assert values in runtime tests.

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

The `demo_jvm.sh` script is a useful utility to compile and run files with the JVM backend with a single command (provide the path to the input source file as an argument). 
- To run the same example as above, run `./demo_jvm.sh tests/runtime/binary_tree.py`

Note that in the above example commands & the `demo_jvm.sh` script all expect the Krakatau directory and this repository's directory to share the same parent - commands will differ if you cloned Krakatau to a different location.

### JVM Backend - Known Issues/Incompatibilities:

- Since bytecode for each class is stored in a separate file, on operating systems with case-insensitive file names you cannot have 2 classes whose names only differ by case.
- Since the main JVM class for a Chocopy program shares the name of the file, do not define other classes with the same name as the source file.
- The special parameter `self` in methods and constructors may not be referenced by a `nonlocal` declaration. The Java equivalent, `this`, is final and cannot be assigned to.
- Some large programs may cause the JVM to run out of stack space, since each frame currently has a hardcoded maximum stack size of 500.
- Integers are compiled to regular ints instead of longs, so this backend will not work on 32-bit JVMs.

## CIL Backend Notes:

The CIL backend for this compiler outputs CIL bytecode in plaintext formatted for the Mono `ilasm` assembler:
1. Use this compiler to generate plaintext bytecode 
    - Format:  `python3 main.py --mode cil <input file> <output dir>`
    - Example: `python3 main.py --mode cil tests/runtime/binary_tree.py .`
2. Run the ilasm assembler to generate `.exe` files - note that this must be done for EACH .cil file generated by the compiler
    - Format:  `ilasm <.cil file>`
    - Example: `ls *.cil | xargs -L1 ilasm`
3. Run the `.exe` files
    - Example: `mono <.exe file>`
    - Example: `mono binary_tree.exe`

The `demo_cil.sh` script is a useful utility to compile and run files with the CIL backend with a single command (provide the path to the input source file as an argument). 
- To run the same example as above, run `./demo_cil.sh tests/runtime/binary_tree.py`

## WASM Backend Notes:

This is WIP, not all features are supported (the binary tree example itself actually does not work, but you can try another one). 

The WASM backend for this compiler outputs WASM in plaintext `.wat` format which can be converted to `.wasm` using `wat2wasm`:
1. Use this compiler to generate plaintext WebAssembly
    - Format:  `python3 main.py --mode wasm <input file> <output dir>`
    - Example: `python3 main.py --mode wasm tests/runtime/binary_tree.py .`
2. Run `wat2wasm` assembler to generate `.wasm` files
    - Format:  `wat2wasm <.wat file> -o <.wasm file>`
    - Example: `wat2wasm binary_tree.wat -o binary_tree.wasm`
3. Run the `.wasm` files using a minimal JS runtime
    - Example: `node wasm.js <.wasm file>`
    - Example: `node wasm.js binary_tree.wasm`

The `demo_wasm.sh` script is a useful utility to compile and run files with the WASM backend with a single command (provide the path to the input source file as an argument). 
- To run the same example as above, run `./demo_wasm.sh tests/runtime/binary_tree.py`

### WASM Backend - Supported Features:
- int, bool, string, list
- most operators
- assignment
- control flow
- stdlib: print, len, and assert
- globals

### WASM Backend - Unsupported Features:
- nonlocal referencing function param
- stdlib: input (node.js does not have synchronous I/O out of the box so this is difficult)

### WASM Backend - Memory Format, Safety, and Management:

- strings (utf-8) - first 4 bytes for length, followed by 1 byte for each character
- lists - first 4 bytes for length, followed by 8 bytes for each element
- ints - i64
- pointers (objects, strings, lists) - i32, where `None` is 0

Strings, lists, objects, and refs holding nonlocals are stored in the heap, aligned to 8 bytes. Right now, memory does not get freed/garbage collected once it is allocated. To provide memory safety, string/list indexing have bounds checking and list operations have a null-check, which crashes the program with a generic "unreachable" instruction.

## FAQ

- What is this for?
  - The primary goal of the project is for me to practice compiler implementation. The secondary goal is to provide a reference to anyone else who is interested in the topics I explore through working on this project - I go into more detail about each part of the compiler on my blog. 
- Why Chocopy?
  - It has a detailed spec and is a relatively small language while being non-trivial enough to offer interesting compiler implementation problems. 
- Why not design your own language?
  - This project is focused on compiler implementation. I want to keep the project very focused and make each addition manageable so that I can make progress in my very limited spare time.
- Why implement this in Python?
  - Since Chocopy is a subset of Python, implementing the compiler in Python means I do not have to write my own lexer and parser. This was explicitly something I wanted to experiment with while writing the frontend, and it worked wonderfully. The secondary reason is that writing it in Python means I can prototype new ideas faster. The lack of type safety in the compiler codebase is mitigated by an extensive test suite.

Most of the test cases are taken from test suites included in the release code for CS164, with some additional tests written for more coverage. Tests include both static validation of generated/annotated ASTs, as well as runtime tests that check the correctness of output code. 
