#!/usr/bin/env python
import sys
import json
import os.path

fileExtension = ".json"
verbose = False

def getCandidates(json):
  ret = []
  if not json.has_key('stats'):
    return ret
  stats = json['stats']
  for stat in stats.itervalues():
    if stat['type'] == "localcandidate" or stat['type'] == "remotecandidate":
      ret.append(stat)
  return ret

def filterCandidates(candidates, ctype):
  ret = []
  for cand in candidates:
    if cand['type'] == ctype:
      ret.append(cand)
  return ret

def filterCandidateType(candidates, cType):
  ret = []
  for cand in candidates:
    if cand['candidateType'] == cType:
      ret.append(cand)
  return ret

def localAndRemoteCandidatesMissing(json, unused):
  candidates = getCandidates(json)
  return len(candidates) == 0

def remoteCandidatesMissing(json, unused):
  candidates = getCandidates(json)
  remoteCandidates = filterCandidates(candidates, "remotecandidate")
  return len(remoteCandidates) == 0

def candidateTypeMissing(json, ctype):
  candidates = getCandidates(json)
  filteredCandidates = filterCandidateType(candidates, ctype)
  return len(filteredCandidates) == 0

initial_db = [
      {
       'name': 'No candidates at all',
       'function': localAndRemoteCandidatesMissing,
       'argument': None,
       'matches': []
      },
      {
       'name': 'Remote candidates missing',
       'function': remoteCandidatesMissing,
       'argument': None,
       'matches': []
      },
      {
       'name': 'Serverreflexive candidates missing',
       'function': candidateTypeMissing,
       'argument': 'serverreflexive',
       'matches': []
      },
      {
       'name': 'Relay candidates missing',
       'function': candidateTypeMissing,
       'argument': 'relayed',
       'matches': []
      }
      ]

def addLogToDb(filename, json, db):
  for entry in db:
    if entry['function'](json, entry['argument']):
      entry['matches'].append(filename)

def loadJsonFile(filename, db):
  dirname = os.path.dirname(filename)
  source = open(filename, 'r')
  parsed = json.loads(source.read())
  addLogToDb(filename, parsed, db)
  source.close()

def dumpDb(db):
  for entry in db:
    print '%d: %s' % (len(entry['matches']), entry['name'])
    if verbose:
      for match in entry['matches']:
        print '\t%s' % match

def main():
  if len(sys.argv) == 1:
    print "Missing input directory name"
    sys.exit(1)
  directories = sys.argv[1:]

  for d in directories:
    for dirName, subdirList, fileList in os.walk(d):
      #print('directory %s' % dirName)
      for fname in fileList:
        if fname.endswith(fileExtension):
          fullname = os.path.join(dirName, fname)
          #print('\t%s' % fullname)
          loadJsonFile(fullname, initial_db)
  dumpDb(initial_db)

if __name__ == "__main__":
  main()
