import evdev
import getopt
from select import select
from sys import argv, exit
from os import system,kill

exitMode = False

modifiers = {
    "ctrl": set((evdev.ecodes.KEY_LEFTCTRL, evdev.ecodes.KEY_RIGHTCTRL)),
    "alt": set((evdev.ecodes.KEY_LEFTALT, evdev.ecodes.KEY_RIGHTALT)),
    "shift": set((evdev.ecodes.KEY_LEFTSHIFT, evdev.ecodes.KEY_RIGHTSHIFT))
}

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
            kill(pid,0)
        except:
            system(deadMonitors[pid][0])
            if deadMonitors[pid][1]:
                exit(1)
            else:
                del deadMonitors[pid]
                break
    updateMonitoring()
    try:
        r, w, x = select(selectList, [], [], 0.25)
        for fd in r:
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
                                system(trig[1])
                                if trig[2]:
                                    exit(0)
    except KeyboardInterrupt:
        exit(0)
    except Exception:
        pass

