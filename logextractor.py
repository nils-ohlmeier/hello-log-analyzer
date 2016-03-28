#!/usr/bin/env python
import sys
import json

def extractLog(filename):
  print filename
  source = open(filename, 'r')
  j = json.loads(source.read())
  source.close()
  for name in ['log', 'localSdp', 'remoteSdp']:
    log = j[name]
    foldedlog = log.replace('\\n', '\n')
    dstfilename = filename[:-4] + name
    dst = open(dstfilename, 'w')
    dst.write(foldedlog)
    dst.close()

if len(sys.argv) == 1:
  print "Missing input file name"
  sys.exit(1)
filename = sys.argv[1]

extractLog(filename)
