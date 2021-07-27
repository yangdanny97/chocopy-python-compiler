base_name="$(basename $1 .py)"

python3 main.py --mode jvm $1 $base_name.j &&
python3 ../Krakatau/assemble.py -q $base_name.j &&
java -cp . $base_name