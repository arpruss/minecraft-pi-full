OPT=/opt/minecraft-pi
BIN=/usr/bin
BASEDIR=$(dirname "$0")
pip install evdev
python $BASEDIR/patch.py $OPT/minecraft-pi $OPT/minecraft-full $BASEDIR/full.txt
chmod 755 $OPT/minecraft-full
cp $BASEDIR/runwithquit.sh $BASEDIR/keymonitor.py $OPT/
sed 's:\./minecraft-pi:sh runwithquit.sh ./minecraft-full:' < $BIN/minecraft-pi > $BIN/minecraft-full
chmod 755 $BIN/minecraft-full
