$* &
main=$!
echo $main
python keymonitor.py "alt+4" "pkill -P $main" exit "alt+f4" "pkill -P $main" exit "ctrl+q" "pkill -P $main" exit
