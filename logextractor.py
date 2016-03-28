#!/usr/bin/env python
import sys
import json
import os.path


def extractLog(filename):
  print filename
  source = open(filename, 'r')
  j = json.loads(source.read())
  log = j['log']
  foldedlog = log.replace('\\n', '\n')
  dstfilename = filename[:-5] + ".log"
  dst = open(dstfilename, 'w')
  dst.write(foldedlog)
  dst.close()
  source.close()


if len(sys.argv) == 1:
  print "Missing input file name"
  sys.exit(1)
filename = sys.argv[1]

extractLog(filename)
