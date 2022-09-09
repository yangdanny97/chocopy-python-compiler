const wasm_path = process.argv[2];

function logString(offset) {
    const length = new Uint32Array(memory.buffer, offset, 1)[0];
    const bytes = new Uint8Array(memory.buffer, offset + 4, Number(length));
    const string = new TextDecoder('utf8').decode(bytes);
    console.log(string);
}

function logInt(val) {
    console.log(Number(val));
}

function logBool(val) {
    console.log(val !== 0);
}

const memory = new WebAssembly.Memory({ initial: 2, maximum: 100 });

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