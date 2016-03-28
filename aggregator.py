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
        'name': 'Log contains "failed to create UDP candidates with error 6"',
        'function': logContains,
        'argument': 'failed to create UDP candidates with error 6',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Local SDP missing',
        'function': sdpEmpty,
        'argument': 'localSdp',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Remote SDP missing',
        'function': sdpEmpty,
        'argument': 'remoteSdp',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'No candidates at all',
        'function': localAndRemoteCandidatesMissing,
        'argument': None,
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Remote candidates missing',
        'function': remoteCandidatesMissing,
        'argument': None,
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains late trickle error "tried to trickle ICE in inappropriate state FAILED"',
        'function': logContains,
        'argument': 'tried to trickle ICE in inappropriate state 5',
        'stopProcessing': False,
        'matches': []
      },
      {
        'name': 'Serverreflexive candidates missing',
        'function': candidateTypeMissing,
        'argument': 'serverreflexive',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Relay candidates missing',
        'function': candidateTypeMissing,
        'argument': 'relayed',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains TCP soccket error ". Abandoning."',
        'function': logContains,
        'argument': '. Abandoning.',
        'stopProcessing': False,
        'matches': []
      },
      {
        'name': 'Log contains "Error in recvfrom: -5961"',
        'function': logContains,
        'argument': 'Error in recvfrom: -5961',
        'stopProcessing': False,
        'matches': []
      },
      {
        'name': 'Unknow',
        'function': None,
        'argument': None,
        'stopProcessing': False,
        'matches': []
      },
      ]

def addLogToDb(filename, json, db):
  for category in db:
    if (not category['function']) or (category['function'](json, category['argument'])):
      newentry = {}
      newentry['filename'] = filename
      newentry['channel'] = json['info']['appUpdateChannel']
      newentry['version'] = json['info']['appVersion']
      newentry['os'] = json['info']['OS']
      category['matches'].append(newentry)
      majorversion = int(newentry['version'].split('.')[0])
      if (not category.has_key('minversion')) or (category['minversion'] > majorversion):
        category['minversion'] = majorversion
      if (not category.has_key('maxversion')) or (category['maxversion'] < majorversion):
        category['maxversion'] = majorversion
      if category['stopProcessing']:
        return

def loadJsonFile(filename, db):
  global read_reports_counter
  dirname = os.path.dirname(filename)
  source = open(filename, 'r')
  parsed = json.loads(source.read())
  addLogToDb(filename, parsed, db)
  read_reports_counter+=1
  source.close()

def writeReport(db):
  for category in db:
    if category.has_key('argument'):
      del category['argument']
    if category.has_key('function'):
      del category['function']
    if category.has_key('stopProcessing'):
      del category['stopProcessing']
  jdb = json.dumps(db)
  report = open(report_file, 'w')
  report.write(jdb)
  report.close()

def displayDb(db):
  print "Analyzed %d reports" % read_reports_counter
  for category in db:
    count = len(category['matches'])
    percent = count / float(read_reports_counter) * 100
    msg = '%d (%04.1f%%):\t' % (count, percent)
    if category['stopProcessing']:
      msg += '* '
    msg += '%s' % (category['name'])
    if category.has_key('minversion'):
      msg += ' [%d - %d]' % (category['minversion'], category['maxversion'])
    print msg
    if verbose:
      for match in category['matches']:
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
  displayDb(initial_db)
  writeReport(initial_db)

if __name__ == "__main__":
  main()
