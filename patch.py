import re
from sys import argv,version_info
import struct

if len(argv) != 4:
    print("usage: python patch.py oldfile newfile patch")
    exit(1)

def fromByte(b):
    if version_info[0] >= 3:
        return b
    else:
        return struct.unpack("B", b)[0]
    
def toByte(x):
    return bytes(bytearray([x]))
    
patch = {}
with open(argv[3],"r") as patchFile:
    for line in patchFile:
        data = re.split(r'\s+', line.strip())
        try:
            location = int(data[0]) - 1
            source = int(data[1],8)
            dest = int(data[2],8)
            patch[location] = (source,dest)
        except:
            pass

with open(argv[1],"rb") as inFile:
    contents = inFile.read()

keys = sorted(patch)

if len(contents) <= max(keys):
    print("Input file too short")
    exit(3)

for key in sorted(patch):
    p = patch[key]
    if fromByte(contents[key]) != p[0]:
        print("Mismatch at offset %u: 0x%x seen, 0x%x needed" % (key,fromByte(contents[key]), p[0]))
        exit(2)

with open(argv[2],"wb") as outFile:
    for i in range(len(contents)):
         outFile.write(toByte(patch[i][1]) if i in patch else toByte(contents[i]))
