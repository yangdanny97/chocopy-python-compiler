/**
 * Runtime support for running WASM compiled from Chocopy
 * 
 * This is a very minimal runtime since the goal was to implement as much as 
 * possible directly in WASM. 
 * 
 * The only imports from JS to WASM are for `console.log` and `console.assert`,
 * and the latter isn't even strictly necessary.
 * 
 * The memory buffer is instantiated by JS, but after that it's never written 
 * to and only used to print strings. 
 */


const wasm_path = process.argv[2];

function logString(offset) {
    // first 4 bytes is the length
    const length = new Uint32Array(memory.buffer, offset, 1)[0];
    // next [length] bytes is the string contents, encoded as utf-8
    const bytes = new Uint8Array(memory.buffer, offset + 4, length);
    const string = new TextDecoder('utf8').decode(bytes);
    console.log(string);
}

function logInt(val) {
    // cast BigInt to a number for pretty-printing w/o the "n"
    // this may truncate or break for values that take >53 bits
    console.log(Number(val));
}

function logBool(val) {
    // this is a 32 bit number, either 1 or 0
    console.log(val !== 0);
}

function assert(val, line) {
    if (!val) {
        throw new Error("Assertion failed on line " + line.toString());
    }
}

const memory = new WebAssembly.Memory({
    initial: 10,
    maximum: 100
});

const importObject = {
    imports: {
        logString: x => logString(x),
        logInt: x => logInt(x),
        logBool: x => logBool(x),
        assert: (x, y) => assert(x, y)
    },
    js: {
        mem: memory
    },
};

const fs = require('fs');

const wasmBuffer = fs.readFileSync(wasm_path);
WebAssembly.instantiate(wasmBuffer, importObject);