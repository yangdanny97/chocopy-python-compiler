# utility for compiling a Chocopy file to .exe files and running it
base_name="$(basename $1 .py)"

rm -f *.cil
rm -f *.exe
python3 main.py --mode cil $1 .
ls *.cil | xargs -L1 ilasm
echo "Running program $base_name..."
mono $base_name.exe