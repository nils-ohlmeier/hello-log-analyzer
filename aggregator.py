#!/usr/bin/env python
import sys
import json
import os.path
from datetime import datetime

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

def logContainsAll(json, strlist):
  ret = True
  for string in strlist:
    ret = ret & logContains(json, string)
  return ret

known_error_db = [
      {
        'name': 'Log contains "failed to create UDP candidates with error 6"',
        'function': logContains,
        'argument': 'failed to create UDP candidates with error 6',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains GetAdaptersInfo failure "Got error from GetAdaptersInfo"',
        'function': logContains,
        'argument': 'Got error from GetAdaptersInfo',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains GetAdaptersInfo failure "Error getting buf len from GetAdaptersAddresses()"',
        'function': logContains,
        'argument': 'Error getting buf len from GetAdaptersAddresses()',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains GetAdaptersInfo failure "Error getting addresses from GetAdaptersAddresses()"',
        'function': logContains,
        'argument': 'Error getting addresses from GetAdaptersAddresses()',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains find local addresses failure "unable to find local addresses"',
        'function': logContains,
        'argument': 'unable to find local addresses',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains error opening registry "Got error 2 opening adapter reg key"',
        'function': logContains,
        'argument': 'Got error 2 opening adapter reg key',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains STS failure "Couldn\'t attach socket to STS"',
        'function': logContains,
        'argument': 'Couldn\'t attach socket to STS',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains candidate creation failure "couldn\'t create any valid candidates"',
        'function': logContains,
        'argument': 'couldn\'t create any valid candidates',
        'stopProcessing': True,
        'matches': []
      },
      {
        'name': 'Log contains HTTP Proxy DNS resolution error "Could not invoke DNS resolver"',
        'function': logContains,
        'argument': 'Could not invoke DNS resolver',
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
        'name': 'Uncategorized',
        'function': None,
        'argument': None,
        'stopProcessing': False,
        'matches': []
      },
      ]
unknown_error_db = [
      {
        'name': 'Log contains late trickle error "tried to trickle ICE in inappropriate state FAILED"',
        'function': logContains,
        'argument': 'tried to trickle ICE in inappropriate state 5',
        'stopProcessing': False,
        'matches': []
      },
      {
        'name': 'Log contains success and failure',
        'function': logContainsAll,
        'argument': ['all checks completed success=1 fail=0', 'all checks completed success=0 fail=1'],
        'stopProcessing': False,
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
        'name': 'Log contains "nr_turn_allocated_cb called with state FAILED"',
        'function': logContains,
        'argument': 'nr_turn_allocated_cb called with state 4',
        'stopProcessing': False,
        'matches': []
      },
      {
        'name': 'Log contains "nr_socket_proxy_tunnel_read unable to connect 407"',
        'function': logContains,
        'argument': 'nr_socket_proxy_tunnel_read unable to connect 407',
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
        return True
  return False

def loadJsonFile(filename, known_db, unknown_db):
  global read_reports_counter
  dirname = os.path.dirname(filename)
  source = open(filename, 'r')
  parsed = json.loads(source.read())
  source.close()
  if not addLogToDb(filename, parsed, known_db):
    addLogToDb(filename, parsed, unknown_db)
  read_reports_counter+=1

def cleanDb(db):
  for category in db:
    if category.has_key('argument'):
      del category['argument']
    if category.has_key('function'):
      del category['function']
    if category.has_key('stopProcessing'):
      del category['stopProcessing']

def writeReport(fd, db):
  cleanDb(db)
  jdb = json.dumps(db)
  fd.write(jdb)
  fd.write('\n')

def createReport(known, unknown):
  report = {'stats': {}}
  report['stats']['date_created'] = datetime.now().isoformat()
  report['stats']['total_number_of_reports'] = read_reports_counter
  cleanDb(known)
  report['known_ice_errors'] = known
  cleanDb(unknown)
  report['uncategorized_ice_errors'] = unknown
  return report

def writeReports(known, unknown):
  report = createReport(known, unknown)
  rfile = open(report_file, 'w')
  rfile.write('var firefox_hello_ice_reports = ')
  j = json.dumps(report)
  rfile.write(j)
  rfile.write('\n')
  rfile.close()

def displayDb(db):
  for category in db:
    count = len(category['matches'])
    percent = count / float(read_reports_counter) * 100
    msg = '  %d (%04.1f%%):\t' % (count, percent)
    msg += '%s' % (category['name'])
    if category.has_key('minversion'):
      msg += ' [%d - %d]' % (category['minversion'], category['maxversion'])
    print msg
    if verbose:
      for match in category['matches']:
        print '\t%s' % match

def displayDbs(known, unknown):
  print "Analyzed %d reports" % read_reports_counter
  print "Known problems:"
  displayDb(known)
  print "Indicators for uncategorized problems:"
  displayDb(unknown)

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
          loadJsonFile(fullname, known_error_db, unknown_error_db)
  displayDbs(known_error_db, unknown_error_db)
  writeReports(known_error_db, unknown_error_db)

if __name__ == "__main__":
  main()
