# utility for compiling a Chocopy file to .class files and running it
base_name="$(basename $1 .py)"

rm -f *.j
rm -f *.class
python3 main.py --mode jvm $1 .
ls *.j | xargs -L1 python3 ../Krakatau/assemble.py -q
echo "Running program $base_name..."
java -cp . $base_name