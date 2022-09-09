const wasm_path = process.argv[2];

// utils for pretty-printing ints, bools, strings

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

const memory = new WebAssembly.Memory({ initial: 10, maximum: 100 });

const importObject = {
    imports: {
        logString: x => logString(x),
        logInt: x => logInt(x),
        logBool: x => logBool(x),
        assert: x => console.assert(x)
    },
    js: { mem: memory },
};

const fs = require('fs');

const wasmBuffer = fs.readFileSync(wasm_path);
WebAssembly.instantiate(wasmBuffer, importObject);