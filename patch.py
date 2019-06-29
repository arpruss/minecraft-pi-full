import re
from sys import argv

if len(argv) != 4:
    print("usage: python patch.py oldfile newfile patch")
    exit(1)
    
patch = {}
with open(argv[3],"r") as patchFile:
    for line in patchFile:
        data = re.split(r'\s+', line.strip())
        try:
            location = int(data[0])
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
    if contents[key] != p[0]:
        print("Mismatch at offset %u." % key)
        exit(2)
    contents[key] = p[1]

with open(argv[1],"wb") as outFile:
    outFile.write(contents)
    