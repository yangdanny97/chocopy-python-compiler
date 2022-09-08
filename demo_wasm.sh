# utility for compiling a Chocopy file to .wasm files and running it
base_name="$(basename $1 .py)"

rm -f *.wat
rm -f *.wasm

python3 main.py --mode wasm $1 .
wat2wasm $base_name.wat -o $base_name.wasm
echo "Running program $base_name..."
node wasm.js $base_name.wasm

