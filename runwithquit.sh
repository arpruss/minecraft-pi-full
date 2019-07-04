BASEDIR=$(dirname "$0")
$* &
main=$!
python $BASEDIR/keymonitormcpipy.py "alt+4" "kill $main" exit "alt+f4" "kill $main" exit "alt+x" "kill $main" exit "dead($main)" "" exit
