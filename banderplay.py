import json
import requests
import time
import sys
import functools
import wget
import os.path

def fetchMetaFiles():
  if not os.path.exists('SegmentMap.json') or not os.path.exists('Bandersnatch.json'):
    print('Downloading metadata...')
    wget.download('https://raw.githubusercontent.com/jolbol1/Bandersnatch/master/SegmentMap.json', 'SegmentMap.json')
    wget.download('https://gist.githubusercontent.com/jonluca/860f3f445e7d84054822276fd058301a/raw/a42b13917332d1667aba47d411f4cb2f4e22f29c/Bandersnatch',
      'Bandersnatch.json')
    print('Done.')

def readSegments():
  with open('SegmentMap.json', "r", encoding = 'utf-8-sig') as read_file:
      sectionsJson = json.load(read_file)
  return  sectionsJson['segments']

def readBanderSnatchData():
  with open('Bandersnatch.json', "r", encoding = 'utf-8-sig') as read_file:
      bandersnatchJson = json.load(read_file)
  value = bandersnatchJson['videos']['80988062']['interactiveVideoMoments']['value']
  return  (value['momentsBySegment'], value['preconditions'], value['segmentGroups']['respawnOptions'])

def execPlayer(cmd):
  request = f"http://127.0.0.1:8080/requests/status.xml?command={cmd}"
  headers = {'Authorization': 'Basic OjEyMzQ1'}
  r = requests.get(request, headers = headers)

def play():
  execPlayer('pl_play')

def goto(offset):
  execPlayer(f'seek&val={offset}')

def pause():
  execPlayer('pl_pause')

def playSeconds(seconds):
  play()
  time.sleep(seconds)
  pause()

def askChoice():
  while True:
    print(', '.join(choices))
    choice = input('> ')
    if choice in choices:
      return choice

def stateSetsForCurrentChoices():
  segmentStateSets = [{}, {}]
  if currentSegmentId in stateSets:
    for segment in stateSets[currentSegmentId]:
      if 'choices' in segment:
        i = 0
        for choice in segment['choices']:
          if 'impressionData' in choice:
            impressionData = choice['impressionData']
            if 'data' in impressionData:
              data = impressionData['data']
              if 'persistent' in data:
                segmentStateSets[i] = data['persistent']
          i = i + 1
  return segmentStateSets

def getStateSetsForSegment(segmentId):
  if segmentId in stateSets:
    for segment in stateSets[segmentId]:
      if 'impressionData' in segment:
        return segment['impressionData']['data']['persistent']
  return {}

def getInitialState():
  return getStateSetsForSegment("1A")

def updateState(segmentStateSet):
  for var in segmentStateSet.keys():
    currentState[var] = segmentStateSet[var]

def updateStateForChoice(choiceIdx):
  segmentStateSets = stateSetsForCurrentChoices()
  if choiceIdx < len(segmentStateSets):
    segmentStateSet = segmentStateSets[choiceIdx]
    updateState(segmentStateSet)

def updateStateForCurrentSegment():
  segmentStateSet = getStateSetsForSegment(currentSegmentId)
  updateState(segmentStateSet)

def preconditionFor(segmentId):
  if segmentId in stateSets:
    for segment in stateSets[segmentId]:
      if 'precondition' in segment:
        return segment['precondition']
  return []

def preconditionsFor(segmentId):
  if segmentId in preconditions:
    return preconditions[segmentId]
  else:
    return []

def allPreconditionsFor(segmentId):
  return preconditionFor(segmentId) + preconditionsFor(segmentId)

def anyPreconditionsFor(segmentId):
  if len(preconditionFor(segmentId)) > 0:
    return preconditionFor(segmentId)
  else:
    return preconditionsFor(segmentId)

def evalPreconditionsWithState(preconditions):
  if len(preconditions) == 0:
    return True
  no = False
  andFlag = False
  orFlag = False
  results = []
  testVar = False
  equal = False
  for p in preconditions:
    if testVar:
      return currentState[p]
    elif type(p) == list:
      results.append(evalPreconditionsWithState(p))
    elif p == 'not':
      no = True
    elif p == 'and':
      andFlag = True
    elif p == 'or':
      orFlag = True
    elif p == 'persistentState':
      testVar = True
    elif p == 'eql':
      equal = True
    elif equal:
      results.append(results.pop() == p)
  if no:
    result = not results.pop()
  elif andFlag:
    result = functools.reduce(lambda a, b: a and b, results)
  elif orFlag:
    result = functools.reduce(lambda a, b: a or b, results)
  else:
    result = results.pop()
  return result

def evalPreconditions(segmentId):
  preconditions = preconditionsFor(segmentId)
  return evalPreconditionsWithState(preconditions)

def filterChoices(choices):
  return list(filter(lambda choice: (evalPreconditions(choice) and
    not any(option['segment'] == choice for option in respawnOptions)), choices))

def test():
  assert(evalPreconditions('8A'))
  assert(not evalPreconditions('8Aa'))
  assert(evalPreconditions('5Q'))
  assert(evalPreconditions('1Qtt_rewatch'))
  assert(not evalPreconditions('1Qnw_rewatch'))
  assert(not evalPreconditions('1QA'))
  assert(not evalPreconditions('ZJ'))
  assert(evalPreconditions('R1'))
  assert(not evalPreconditions('2Bp1'))
  print("Test OK")

fetchMetaFiles()
segments = readSegments()
(stateSets, preconditions, respawnOptions) = readBanderSnatchData()
currentSegmentId = '1A'
currentState = getInitialState()

if len(sys.argv) > 1 and sys.argv[1] == "test":
  test()
else:
  while True:
    currentSegment = segments[currentSegmentId]
    choices = filterChoices(currentSegment['next'].keys())
    startTimeSec = currentSegment['startTimeMs'] / 1000
    if not 'endTimeMs' in currentSegment:
      break
    endTimeSec = currentSegment['endTimeMs'] / 1000
    goto(int(startTimeSec))
    playSeconds(endTimeSec - startTimeSec + 1)
    if len(choices) == 0:
      break
    else:
      if len(choices) == 1:
        choiceIdx = 0
        currentSegmentId = choices[choiceIdx]
        print(f"Auto-choosing segment {currentSegmentId}")
      else:
        nextSegmentId = askChoice()
        choiceIdx = choices.index(nextSegmentId)
        currentSegmentId = nextSegmentId
      updateStateForChoice(choiceIdx)
      updateStateForCurrentSegment()
print("The End")
