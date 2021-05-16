from chinese import ChineseAnalyzer
from readings import init as initReadings
from cccanto import init as initDict
import itertools as it

readings = initReadings('cccedict-canto-readings-150923.txt')
cdict = initDict('cccanto-webdist.txt')

analyzer = ChineseAnalyzer()

lines = """大香港精神

行開啲啦一個二個"""

for line in lines.strip().splitlines():
  if len(line) == 0:
    continue
  print(f'## {line}')
  result = analyzer.parse(line, traditional=True)

  for tokenIdx, token in enumerate(result.tokens()):
    print(f'### {token}')
    for hitIdx, hit in enumerate(result[token]):
      if len(result[token]) > 1:
        print(f"#### {hitIdx}")

      print(hit)
      for aIdx, accum in enumerate(it.accumulate(result.tokens()[tokenIdx:])):
        checkReadings = accum in readings
        checkDict = accum in cdict
        if checkReadings:
          print(f"READINGS={accum}", readings[accum])
        if checkDict:
          print(f"CANTO DICT={accum}", cdict[accum])
        if not (checkDict or checkReadings):
          # stop searching for longer runs of text
          break
