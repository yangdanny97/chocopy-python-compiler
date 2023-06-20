# utility for compiling a Chocopy file to LLVM IR and running it
base_name="$(basename $1 .py)"

rm -f *.ll
rm -f *.s

python3 main.py --mode llvm $1 .
lli $base_name.ll


