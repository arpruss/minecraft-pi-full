$* &
main=$!
echo $main
python keymonitor.py "ctrl+q" "pkill -P $main" exit
echo kill -9 $monitor
