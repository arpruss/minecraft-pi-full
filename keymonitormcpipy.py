import evdev
import getopt
import pyosd
from evdev import ecodes as ecodes
from select import select
from sys import argv, exit
import signal
import subprocess
import os

osd = pyosd.osd()

exitMode = False

modifiers = {
    "ctrl": set((evdev.ecodes.KEY_LEFTCTRL, evdev.ecodes.KEY_RIGHTCTRL)),
    "alt": set((evdev.ecodes.KEY_LEFTALT, evdev.ecodes.KEY_RIGHTALT)),
    "shift": set((evdev.ecodes.KEY_LEFTSHIFT, evdev.ecodes.KEY_RIGHTSHIFT)) }

decode = {ecodes.KEY_SEMICOLON:';',ecodes.KEY_APOSTROPHE:"'",
        ecodes.KEY_GRAVE:'`',ecodes.KEY_MINUS:'-',ecodes.KEY_EQUAL:'=',
        ecodes.KEY_LEFTBRACE:'[',ecodes.KEY_RIGHTBRACE:']',
        ecodes.KEY_BACKSLASH:'\\',
        ecodes.KEY_COMMA:',',ecodes.KEY_DOT:'.',ecodes.KEY_SLASH:'/',ecodes.KEY_SPACE:' '}
decode_shift = {ecodes.KEY_SEMICOLON:':',ecodes.KEY_APOSTROPHE:'"',
        ecodes.KEY_GRAVE:'~',ecodes.KEY_MINUS:'_',ecodes.KEY_EQUAL:'+',
        ecodes.KEY_LEFTBRACE:'{',ecodes.KEY_RIGHTBRACE:'}',
        ecodes.KEY_BACKSLASH:'|',
        ecodes.KEY_COMMA:'<',ecodes.KEY_DOT:'>',ecodes.KEY_SLASH:'?',ecodes.KEY_SPACE:' '}

for i in range(26):
    lc = chr(ord('a')+i)
    uc = chr(ord('A')+i)
    code = getattr(ecodes,"KEY_"+uc)
    decode[code] = lc
    decode_shift[code] = uc
for i in range(10):
    c = chr(ord('0')+i)
    code = getattr(ecodes,"KEY_"+c)
    decode[code] = c
    decode_shift[code] = {'1':'!', '2':'@', '3':'#', '4':'$', '5':'%',
            '6':'^','7':'&','8':'*','9':'(','0':')'}[c]

grabbed = []
typed = ""
keysDown = set()

def modifierPressed(mod):
    for m in mod:
        if m in keysDown:
            return True
    return False

class KeyDescription(object):
    def __init__(self, key, modifiers=[]):
        self.modifiers = modifiers
        self.key = key
        
    def __repr__(self):
        return repr(self.modifiers)+","+repr(self.key)
        
    def pressed(self, lastKey):
        if lastKey == self.key:
            for m in self.modifiers:
                if not modifierPressed(m):
                    return False
            for m in modifiers:
                if modifiers[m] not in self.modifiers and modifierPressed(modifiers[m]):
                    return False
            return True
        return False

triggers = []
deadMonitors = {}

monitored = []
selectList = {}

def getKeyboardDevices():
    devices = []
    for d in (evdev.InputDevice(path) for path in evdev.list_devices()):
        c = d.capabilities()
        for t in triggers:
             if t[0].key in c.get(evdev.ecodes.EV_KEY,[]): #('EV_KEY', 1),[]):
                 devices.append(d)
                 break
    return devices

def updateMonitoring():
    global monitored,selectList
    current = getKeyboardDevices()
    changed = False
    for d in current:
        if d not in monitored:
            changed = True
            break
    if not changed:
        for d in monitored:
            if d not in current:
                changed = True
    if changed:
        monitored = current
        print("Monitoring "+str(monitored))
        selectList = {d.fd:d for d in current}
    return changed

def help():
    print("Usage: python keymonitor.py key1 command1 [exit] [key2 command2 [exit]] ...]")
    exit(0)

def parseKey(k):
    k = k.replace(" ", "")
    kk = k.split("+")
    mod = []
    for m in kk[:-1]:
        mod.append(modifiers[m])
    kd = KeyDescription(getattr(evdev.ecodes, "KEY_" + kk[-1].upper()), modifiers=mod) 
    return kd

def showTyped():
    if typed:
        osd.display(typed+"_")
    else:
        osd.display("")

lastProcess = None

def runScript(s):
    global lastProcess
    split = s.split(" ",2)
    if len(split) < 1:
        return
    if split[0].startswith("/py"):
        if lastProcess is not None:
            try:
                os.system("pkill -9 -P %d"%lastProcess.pid)
                #os.kill(lastProcess.pid,signal.SIGKILL)
                lastProcess.wait()
            except:
                pass
            lastProcess = None
        if len(split) < 2:
            return
        cmd = "cd ~/mcpipy && python3 "+split[1]+".py"+(" "+split[2:] if len(split)>2 else "")
        try:
            N1 = open(os.devnull, "w")
            print(cmd)
            lastProcess = subprocess.Popen(["sh","-c",cmd],stdout=N1,stderr=subprocess.STDOUT,close_fds=True)
        except:
            print("Error running")
 
pos = 1

while pos+1 < len(argv):
    deadPid = None
    if argv[pos].startswith("dead"):
       deadPid = int(argv[pos][4:].replace(" ","").replace("(","").replace(")",""))
    else:
       k = parseKey(argv[pos])
    c = argv[pos+1]
    e = False
    if pos+2 < len(argv) and argv[pos+2] == "exit":
        e = True
        pos += 1
    if deadPid is None:
        triggers.append((k,c,e))
    else:
        deadMonitors[deadPid] = (c,e)
    pos += 2
        
if not triggers and not deadMonitors:
    help()

while True:
    for pid in deadMonitors:
        try:
            os.kill(pid,0)
        except:
            os.system(deadMonitors[pid][0])
            if deadMonitors[pid][1]:
                exit(1)
            else:
                del deadMonitors[pid]
                break
    updateMonitoring()
    try:
        r, w, x = select(selectList, [], [], 0.25)
        for fd in r:
            currentDevice = None
            for dev in monitored:
                if fd == dev.fd:
                    currentDevice = dev
            for event in selectList[fd].read():
                if event.type == evdev.ecodes.EV_KEY:
                    if not event.value:
                        if event.code in keysDown:
                            keysDown.remove(event.code)
                    else:
                        keysDown.add(event.code)
                    if event.value:
                        for trig in triggers:
                            if trig[0].pressed(event.code):
                                os.system(trig[1])
                                if trig[2]:
                                    exit(0)
                    if currentDevice and event.type == evdev.ecodes.EV_KEY and not event.value:
                        if currentDevice in grabbed:
                            if event.code == ecodes.KEY_ESC:
                                typed = ""
                                showTyped()
                                currentDevice.ungrab()
                                grabbed.remove(currentDevice)
                            elif event.code == ecodes.KEY_BACKSPACE:
                                if typed:
                                    typed = typed[:-1]
                                    showTyped()
                                    if not typed:
                                        currentDevice.ungrab()
                                        grabbed.remove(currentDevice)
                            elif event.code in (ecodes.KEY_ENTER,ecodes.KEY_KPENTER):
                                s = typed
                                typed = ""
                                showTyped()
                                currentDevice.ungrab()
                                grabbed.remove(currentDevice)
                                runScript(s)
                            else:
                                try:
                                    typed += decode_shift[event.code] if modifierPressed(modifiers["shift"]) else decode[event.code]
                                    showTyped()
                                except KeyError:
                                    pass
                        elif event.code == ecodes.KEY_SLASH:
                            grabbed.append(currentDevice)
                            currentDevice.grab()
                            typed = "/"
                            showTyped()

    except KeyboardInterrupt:
        exit(0)
    #except Exception:
        #pass

