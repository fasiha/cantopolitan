from chinese import ChineseAnalyzer
from readings import init as initReadings
from cccanto import init as initDict
import itertools as it
import typing
import re
import sys
from cache_analysis import cache_analysis
from wordfill import fill as wordfill

readings = initReadings('cccedict-canto-readings-150923.txt')
cdict = initDict('cccanto-webdist.txt')
ANALYSIS_CACHE_FILE = 'analysis_cache.pickle'
analyzer = ChineseAnalyzer()


def cleanPinyin(pinyin: typing.Optional[list[str]]) -> typing.Optional[str]:
  if pinyin is None:
    return None
  return " ".join(pinyin)


def noneSetToNone(s: set[typing.Optional[str]]) -> typing.Optional[set[str]]:
  if len(s) == 1 and (None in s):
    return None
  return {elt for elt in s if elt is not None}


class Morpheme(typing.TypedDict):
  hanzi: str
  pinyin: typing.Optional[set[str]]
  canto: typing.Optional[set[str]]


def mergeMorphemes(ms: list[Morpheme], cantos: set[str]) -> Morpheme:
  hanzi = "".join(m['hanzi'] for m in ms)
  pinyin: set[str] = set()
  for m in ms:
    pinyin |= m['pinyin'] or set()
  return Morpheme(hanzi=hanzi, pinyin=pinyin, canto=cantos)


def accumulate(key: str):
  return readings[key] if key in readings else None, cdict[key] if key in cdict else None


def allSubwords(s: str):
  """
  Given a string, return an iterator that gives all contiguous substrings.

  For `abc`, you get
  - `a`
  - `ab`
  - `abc`
  - `b`
  - `bc`
  - `c`
  """
  return it.chain.from_iterable(it.accumulate(s[i:]) for i in range(len(s)))


def hanziToCantos(key: str) -> set[str]:
  s: set[str] = set()
  s |= set(entry[1] for entry in cdict[key]) if key in cdict else set()
  s |= set(entry[1] for entry in readings[key]) if key in readings else set()
  return s


# I want to emphasize that these are guessed
def reformatGuessedCantos(s: set[str]) -> set[str]:
  return set(map(lambda s: '¿' + ' -'.join(s.split(' ')), s))


# There are going to be words where we didn't find Cantonese readings.
# Break down these morphemes into individual pieces and try to find dictionary entries for these.
# Prefer the longest dictionary hit. This is risky!
def guessMissingReadings(morphemes: list[Morpheme]):
  # Step 1: build a small dictionary of all sub-words (spanning morpheme boundaries)
  guessNeededPredicate: typing.Callable[
      [Morpheme], bool] = lambda m: bool(m['canto'] or len(m['hanzi'].strip()))
  missing: set[str] = set()
  for i, morpheme in enumerate(morphemes):
    if guessNeededPredicate(morpheme):
      continue
    adjacent = list(it.takewhile(lambda m: not guessNeededPredicate(m), morphemes[i:]))
    for hanzi in allSubwords("".join(m['hanzi'] for m in adjacent)):
      if hanzi in missing:
        continue
      if hanzi in cdict or hanzi in readings:
        missing.add(hanzi)

  # Step 2: find the largest words to "fill" a morpheme
  i = 0
  while i < len(morphemes):
    morpheme = morphemes[i]
    if guessNeededPredicate(morpheme):
      i += 1
      continue
    found = [k for k in allSubwords(morpheme['hanzi']) if k in missing]
    mash = "".join(found)
    if not all(char in mash for char in morpheme['hanzi']):
      i += 1
      continue
    # we have a hit for all characters in hanzi. Fill in the "biggest" first, greedily
    pieces = wordfill(morpheme['hanzi'], found)

    newMorphemes = [
        Morpheme(hanzi=p, pinyin=None, canto=reformatGuessedCantos(hanziToCantos(p)))
        for p in pieces
    ]
    morphemes[i:i + 1] = newMorphemes
    i += len(pieces)


ChineseAnalyzerResult = typing.Any

linesResults: list[tuple[str, typing.Optional[ChineseAnalyzerResult]]] = []
with cache_analysis(ANALYSIS_CACHE_FILE, analyzer) as cache:
  for line in sys.stdin.readlines():
    if len(line) == 0:
      result = None
    else:
      if line in cache:
        result = cache[line]
      else:
        result = analyzer.parse(line, traditional=True)
        cache[line] = result

    linesResults.append((line, result))

parsed: list[list[Morpheme]] = []
for line, result in linesResults:
  if result is None:
    parsed.append([Morpheme(hanzi='', pinyin=None, canto=None)])
    continue

  print(f'## {line}')

  morphemes = [
      Morpheme(
          hanzi=str(token),
          pinyin=noneSetToNone({cleanPinyin(hit.pinyin) for hit in result[token]}),
          canto=None) for token in result.tokens()
  ]

  startIdx = 0
  while startIdx < len(morphemes):
    accumulated = [
        (idx + 1, accumulate(accum))
        for idx, accum in enumerate(it.accumulate(p['hanzi'] for p in morphemes[startIdx:]))
    ]
    accumulated = [a for a in accumulated if a[1][0] or a[1][1]]
    if len(accumulated) == 0:
      startIdx += 1
      continue

    cantoReading, cantoEntry = accumulated[-1][1]

    pinyinCantos: list[tuple[str, str]] = []
    if cantoReading:
      pinyinCantos.extend((pinyin, canto) for pinyin, canto in cantoReading)
    if cantoEntry:
      pinyinCantos.extend((pinyin, canto) for pinyin, canto, english in cantoEntry)

    numAccum = accumulated[-1][0]
    morpheme = morphemes[startIdx]
    if numAccum == 1 and morpheme['pinyin']:
      cantos = {canto for pinyin, canto in pinyinCantos if pinyin in (morpheme['pinyin'] or {})}
    else:
      cantos = {canto for pinyin, canto in pinyinCantos}

    replaceSlice = slice(startIdx, startIdx + numAccum)
    morphemes[replaceSlice] = [mergeMorphemes(morphemes[replaceSlice], cantos)]
    startIdx += 1

  guessMissingReadings(morphemes)

  print(morphemes)
  parsed.append(morphemes)
  # ABOVE: used for ruby analysis later

  # BELOW: printout for definitions and general insight into parsing
  for tokenIdx, token in enumerate(result.tokens()):
    print(f'### {token}')
    for hitIdx, hit in enumerate(result[token]):
      if len(result[token]) > 1:
        print(f"#### {hitIdx}")

      print(hit)
      accumulatedFound = 0
      for accum in it.accumulate(result.tokens()[tokenIdx:]):
        checkReadings = accum in readings
        checkDict = accum in cdict
        if checkReadings:
          print(f"READINGS={accum}", readings[accum])
        if checkDict:
          print(f"CANTO DICT={accum}", cdict[accum])
        if not (checkDict or checkReadings):
          # stop searching for longer runs of text
          break
        accumulatedFound += 1
      if accumulatedFound == 0 and hit.pinyin is None:
        # this wasn't found in either Canto dataset, and no pinyin
        # ok for punctuation though
        print('NO READINGS FOUND')

print(parsed)


def cantoneseToHtml(c: str) -> str:
  num = re.compile('[0-9]$')
  match = num.search(c)
  if not match:
    return c
  word = c[:match.start()]
  tone = c[match.start():]
  return f'{word}<sup>{tone}</sup>'


def morphemeToRuby(m: Morpheme) -> str:
  if m['canto'] is None:
    return m['hanzi']

  more = '' if len(m['canto']) == 1 else '<sup>+</sup>'
  canto: str = min(m['canto'], default='unknown')
  cantos = canto.split(' ')
  if len(cantos) == len(m['hanzi']):
    hanzis = iter(m['hanzi'])
    return "".join(
        f"<ruby>{h}<rt>{cantoneseToHtml(c)}{more}</rt></ruby>" for h, c in zip(hanzis, cantos))

  canto = canto.replace(' ', '')
  return f'<ruby>{m["hanzi"]}<rt>{canto}{more}</rt></ruby>'


ruby = "".join("".join(map(morphemeToRuby, line)) for line in parsed)
print("# Readings as HTML")
print(ruby)
