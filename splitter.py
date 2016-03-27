#!/usr/bin/env python
import sys
import json
import os.path
import hashlib

logFileNameID = ".v2.log."

def splitlogfile(filename):
  dirname = os.path.dirname(filename)
  source = open(filename, 'r')
  for line in source:
    uuid, log = line.split('\t', 1)
    md5sum = hashlib.md5(log).hexdigest()
    parsed = json.loads(log)
    #print parsed['localSdp']
    pretty = json.dumps(parsed, indent=2)
    #pnew = pretty.replace('\\n', '\\n\"\n\"')
    pnew = pretty
    dstfile = "%s.%s.json" % (uuid, md5sum)
    dstfullname = os.path.join(dirname, dstfile)
    print "Creating %s" % (dstfullname)
    if os.path.isfile(dstfullname):
      print "Ignoring duplicate report for %s !!!!" % (dstfullname)
      continue
    dest = open(dstfullname, 'w')
    dest.write(pnew)
    dest.close()
  source.close()

if len(sys.argv) == 1:
  print "Missing input directory name"
  sys.exit(1)
directories = sys.argv[1:]

for d in directories:
  for dirName, subdirList, fileList in os.walk(d):
    print('directory %s' % dirName)
    for fname in fileList:
      if logFileNameID in fname:
        fullname = os.path.join(dirName, fname)
        print('\t%s' % fullname)
        splitlogfile(fullname)
