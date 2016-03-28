#!/usr/bin/env python
import sys
import json
import os.path

file_extension = ".json"
verbose = False
read_reports_counter = 0
report_file = "report.json"

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

def sdpEmpty(json, sdp):
  return len(json[sdp]) == 0

def logContains(json, string):
  return string in json['log']

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
      },
      {
       'name': 'Local SDP missing',
       'function': sdpEmpty,
       'argument': 'localSdp',
       'matches': []
      },
      {
       'name': 'Remote SDP missing',
       'function': sdpEmpty,
       'argument': 'remoteSdp',
       'matches': []
      },
      {
       'name': 'Log contains TCP soccket error ". Abandoning."',
       'function': logContains,
       'argument': '. Abandoning.',
       'matches': []
      },
      {
       'name': 'Log contains "failed to create UDP candidates with error 6"',
       'function': logContains,
       'argument': 'failed to create UDP candidates with error 6',
       'matches': []
      },
      {
       'name': 'Log contains "Error in recvfrom: -5961"',
       'function': logContains,
       'argument': 'Error in recvfrom: -5961',
       'matches': []
      },
      ]

def addLogToDb(filename, json, db):
  for entry in db:
    if entry['function'](json, entry['argument']):
      newentry = {}
      newentry['filename'] = filename
      newentry['channel'] = json['info']['appUpdateChannel']
      newentry['version'] = json['info']['appVersion']
      newentry['os'] = json['info']['OS']
      entry['matches'].append(newentry)

def loadJsonFile(filename, db):
  global read_reports_counter
  dirname = os.path.dirname(filename)
  source = open(filename, 'r')
  parsed = json.loads(source.read())
  addLogToDb(filename, parsed, db)
  read_reports_counter+=1
  source.close()

def writeReport(db):
  for entry in db:
    if entry.has_key('argument'):
      del entry['argument']
    if entry.has_key('function'):
      del entry['function']
  jdb = json.dumps(db)
  report = open(report_file, 'w')
  report.write(jdb)
  report.close()

def displayDb(db):
  print "Analyzed %d reports" % read_reports_counter
  for entry in db:
    count = len(entry['matches'])
    percent = count / float(read_reports_counter) * 100
    print '%d (%04.1f%%):\t%s' % (count, percent, entry['name'])
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
        if fname.endswith(file_extension):
          fullname = os.path.join(dirName, fname)
          #print('\t%s' % fullname)
          loadJsonFile(fullname, initial_db)
  writeReport(initial_db)
  displayDb(initial_db)

if __name__ == "__main__":
  main()
