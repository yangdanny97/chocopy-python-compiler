const wasm_path = process.argv[2];

function logString(offset) {
    const length = 0;
    // TODO: get length from buffer
    const bytes = new Uint8Array(memory.buffer, offset, length);
    const string = new TextDecoder('utf8').decode(bytes);
    console.log(string);
}

function logInt(val) {
    console.log(Number(val));
}

function logBool(val) {
    console.log(val !== 0);
}

const importObject = {
    imports: {
        logString: x => logString(x),
        logInt: x => logInt(x),
        logBool: x => logBool(x),
        assert: x => console.assert(x)
    }
};

const fs = require('fs');

const wasmBuffer = fs.readFileSync(wasm_path);
WebAssembly.instantiate(wasmBuffer, importObject);