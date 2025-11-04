# chocopy-python-compiler

[![pyrefly](https://img.shields.io/endpoint?url=https://pyrefly.org/badge.json)](https://github.com/facebook/pyrefly)

Ahead-of-time compiler for [Chocopy](https://chocopy.org/), a subset of Python 3.6 with type annotations and static type checking. 

Chocopy is used in compiler courses at several universities. This project has no relation to those courses, and is purely for my own learning/practice/fun. 

Progress is documented on my [blog](https://yangdanny97.github.io/blog/):
- [Part 1: Frontend/Typechecker](https://yangdanny97.github.io/blog/2020/05/29/chocopy-typechecker)
- [Part 2: JVM backend](https://yangdanny97.github.io/blog/2021/08/26/chocopy-jvm-backend)
- [Part 3: CIL backend](https://yangdanny97.github.io/blog/2022/05/22/chocopy-cil-backend)
- [Part 4: WASM backend](https://yangdanny97.github.io/blog/2022/10/11/chocopy-wasm-backend)
- [Part 5: LLVM backend](https://yangdanny97.github.io/blog/2023/07/18/chocopy-llvm-backend)

## Features

This compiler is written entirely in Python. Since Chocopy is itself a subset of Python, lexing and parsing can be entirely handled by Python's `ast` module.

The frontend of this compiler matches the functionality of the first 2 passes (parsing & typechecking) Chocopy's reference compiler implementation, and outputs the AST in a JSON format that is compatible with the reference implementation's backend. That means that you can parse and typecheck the Chocopy file with this compiler, then use the reference implementation's backend to handle assembly code generation.

This compiler contains multiple backends not found in the reference implementation: 
- Untyped Python 3 source code
- JVM bytecode, formatted for the Krakatau assembler
- CIL bytecode, formatted for the Mono ilasm assembler
- WASM, in WAT format
- LLVM IR, in text format

The test suite includes both static validation of generated/annotated ASTs, as well as runtime tests that actually execute the output programs to check correctness. Many of the AST validation test cases are taken from test suites included in the release code for Berkeley's CS164, with some additional tests written for more coverage.

## Requirements:
- Python 3.11
- JVM Backend Requirements:
  - [Krakatau JVM Assembler](https://github.com/Storyyeller/Krakatau)
  - Tested with Java 8, using Krakatau V1 (the one written in Python, not Rust)
- CIL Backend Requirements:
  - [Mono](https://www.mono-project.com/)
  - Tested with Mono 6.12
- WASM Backend Requirements:
  - [WebAssembly Binary Toolkit (wabt)](https://github.com/WebAssembly/wabt), specifically the `wat2wasm` tool
  - NodeJS for the runtime
- LLVM Backend Requirements
  - LLVM toolchain
  - `llvmlite`
  - Tested with LLVM 16.0.6

## Usage

Invoke `main.py` with the appropriate flags, plus the input file (required) and output file (optional). 

The input file should have extension `.py`. If the output file is not provided, then outputs will depend on the input file name:
- AST JSON outputs will be written to a file of the same name/location as the input file, with extension `.py.ast`
- Python source outputs will be written to a file of the same name/location as the input file, with extension `.out.py`
- JVM outputs will be written to the same location as the input file, with the extension `.j`
- CIL outputs will be written to the same location as the input file, with the extension `.cil`
- WASM outputs will be written to the same location as the input file, with the extension `.wat`

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
    - `wasm` - output WASM as plaintext in WAT format
    - `llvm` - output LLVM IR in text format

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

### JVM Backend - Incompatibilities:

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

### CIL Backend - Incompatibilities
- Since the main CIL class for a Chocopy program shares the name of the file, do not define other classes with the same name as the source file.

## WASM Backend Notes:

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

The `wasm.js` file contains all the runtime support needed to run the WASM generated by this compiler. This backend was designed was to minimize runtime JavaScript dependencies, so the only imported functions are for assertions and printing strings/integers/booleans.

### WASM Backend - Incompatibilities:
- `input` stdlib function is not supported (node.js does not support synchronous I/O)

### WASM Backend - Memory Format, Safety, and Management:

- strings (utf-8) - first 4 bytes for length, followed by 1 byte for each character
- lists - first 4 bytes for length, followed by 8 bytes for each element
- ints - i64
- pointers (objects, strings, lists) - i32, where `None` is 0
- objects - first 4 bytes for vtable addr, followed by 8 bytes for each attribute. inherited attribute/method positions are same as parent.

Strings, lists, objects, and refs holding nonlocals are stored in the heap, aligned to 8 bytes. Right now, memory does not get freed/garbage collected once it is allocated, so large programs may run out of memory.

To provide memory safety, string/list indexing have bounds checking and list operations have a null-check, which crashes the program with a generic "unreachable" instruction.

## LLVM Backend Notes:

The LLVM backend for this compiler outputs LLVM IR in plaintext `.ll` format which can be compiled using `llc` or interpreted using `lli`:
1. Use this compiler to generate plaintext LLVM IR
    - Format:  `python3 main.py --mode llvm <input file> <output dir>`
    - Example: `python3 main.py --mode llvm tests/runtime/binary_tree.py .`
2. Run the `.ll` files using `lli`
    - Example: `lli <.ll file>`
    - Example: `lli binary_tree.ll`

The `demo_llvm.sh` script is a useful utility to compile and run files with the LLVM backend with a single command (provide the path to the input source file as an argument). 
- To run the same example as above, run `./demo_llvm.sh tests/runtime/binary_tree.py`

Generated programs should only depend on the C standard library, so there's no custom runtime to link to. 

### LLVM Backend - Incompatibilities:
- `input` stdlib function - inputs are truncated to 100 characters and newlines are not permitted
- strings are required to be ASCII
- top-level statements are grouped under the `main` function - do not define any functions called `main` in your program, and do not shadow any function names from the C standard library

### LLVM Backend - Memory Format, Safety, and Management:

- strings - null-terminated `char*`, same as C strings
- lists - first 4 bytes for length, followed by the contents as a packed array
- ints - 32 bits
- pointers (objects, strings, lists) - same as C pointers, where `None` is the null pointer
- objects - struct containing vtable address followed by attributes

Memory does not get freed/garbage collected once it is allocated, so large programs may run out of memory. 

To provide some memory safety, string/list indexing have bounds checking and list operations have a null-check. Unlike the WASM backend, bounds checking and null checks have their own error messages and display a line number similar to assertions.

Error handling is done using the `setjmp`/`longjmp` strategy, with the error code and line saved in global variables.

## FAQ

- What is this for?
  - The primary goal of the project is for me to practice compiler implementation. The secondary goal is to provide a reference to anyone else who is interested in the topics I explore through working on this project - I go into more detail about each part of the compiler on my blog. 
- Why Chocopy?
  - It has a detailed spec and is a relatively small language while being non-trivial enough to offer interesting compiler implementation problems. For example: arrays, inheritance/dynamic dispatch, nested functions, etc.
- Why not design your own language?
  - This project is focused on compiler implementation. I want to keep the project very focused and make each addition manageable so that I can make progress in my very limited spare time.
- Why implement this in Python?
  - Since Chocopy is a subset of Python, implementing the compiler in Python means I do not have to write my own lexer and parser. This was explicitly something I wanted to experiment with while writing the frontend, and it worked wonderfully. The secondary reason is that writing it in Python means I can prototype new ideas faster. The lack of type safety in the compiler codebase is mitigated by an extensive test suite.

Most of the test cases are taken from test suites included in the release code for CS164, with some additional tests written for more coverage. Tests include both static validation of generated/annotated ASTs, as well as runtime tests that check the correctness of output code. 
