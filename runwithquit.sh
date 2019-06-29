BASEDIR=$(dirname "$0")
$* &
main=$!
python $BASEDIR/keymonitor.py "alt+4" "kill $main" exit "alt+f4" "kill $main" exit "ctrl+q" "kill $main" exit "dead($main)" "" exit
