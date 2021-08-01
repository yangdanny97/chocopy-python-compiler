base_name="$(basename $1 .py)"

rm *.j
rm *.class
python3 main.py --mode jvm $1 .
ls *.j | xargs -L1 python3 ../Krakatau/assemble.py -q
java -cp . $base_name