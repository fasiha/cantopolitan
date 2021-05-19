from chinese import ChineseAnalyzer
from readings import ReadingEntry, init as initReadings
from cccanto import CantoEntry, init as initDict
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
  pinyins: list[
      typing.Optional[str]]  # Jieba's hits per token, so at least 1, maybe more; all maybe None
  definitions: list[typing.Optional[list[str]]]  # same as above
  cantoDefinitions: list[CantoEntry]  # matched by hanzi
  cantoPinyins: list[ReadingEntry]  # also matched by hanzi but for comparison to pinyins
  # len(cantoDefinitions) might be != len(cantoPinyins)!
  merged: bool  # should default to false; when we create a new morpheme from multiple ones, set this to true
  hidden: bool  # should default to false; when a merged morpheme overshadows a Jieba morpheme, hide the latter


def initMorpheme(hanzi: str) -> Morpheme:
  return Morpheme(
      hanzi=hanzi,
      pinyins=[],
      definitions=[],
      cantoDefinitions=[],
      cantoPinyins=[],
      merged=False,
      hidden=False)


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
  s |= set(entry['cantonese'] for entry in cdict[key]) if key in cdict else set()
  s |= set(entry['cantonese'] for entry in readings[key]) if key in readings else set()
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

parsed: list[typing.Optional[list[Morpheme]]] = []
# outer list: lines
# inner list: morphemes or nothing (empty line)

for line, result in linesResults:
  if result is None:
    parsed.append(None)
    continue

  print(f'## {line}')

  morphemes: list[Morpheme] = []
  for token in result.tokens():
    morpheme = initMorpheme(token)
    for hit in result[token]:
      morpheme['pinyins'].append(cleanPinyin(hit.pinyin) if hit.pinyin else None)
      morpheme['definitions'].append(hit.definitions)
    morpheme['cantoDefinitions'] = cdict[token] if token in cdict else []
    morpheme['cantoPinyins'] = readings[token] if token in readings else []
    morphemes.append(morpheme)

  # This list of morphemes may have a few things wrong with it:
  # 1. Instead of one morpheme object per real morpheme, Jieba might have given us TWO or more. We need the user to downselect for us.
  # 2. We might be able to consolidate multiple morphemes into a single one if we find a run of them in the CC-Canto.
  # 3. We *definitely* don't have any Cantonese readings

  # Let's try to do #2: loop thru the list of tokens and see if we can consolidate more than one element
  startIdx = 0
  while startIdx < len(morphemes):
    numAccumulated = 0

    accumulatingHanzi: enumerate[str] = enumerate(
        it.accumulate(m['hanzi'] for m in morphemes[startIdx:]))
    accumulatingEntries = [(idx, cdict[h] if h in cdict else None) for (idx, h) in accumulatingHanzi
                          ]
    # find longest run of morphemes' hanzi in dictionary
    for idx, entries in reversed(accumulatingEntries):
      if entries is None:
        continue
      # first non-None entry
      if idx == 0:
        # same hits as above, longer hit not found
        break
      # longest non-boring hit found!

      numAccumulated = idx + 1
      for oldMorpheme in morphemes[startIdx:startIdx + numAccumulated]:
        oldMorpheme['hidden'] = True

      newMorpheme = Morpheme(
          hanzi=entries[0]['hanzi'],
          pinyins=[],
          definitions=[],
          cantoPinyins=[],
          cantoDefinitions=entries,
          merged=True,
          hidden=False)
      morphemes.insert(startIdx, newMorpheme)
      break

    startIdx += (numAccumulated + 1)
    # skip all accumulated morphemes and the one we just inserted

  # guessMissingReadings(morphemes)

  import json
  print(json.dumps(morphemes, ensure_ascii=False))
  parsed.append(morphemes)


def cantoneseToHtml(c: str) -> str:
  num = re.compile('[0-9]$')
  match = num.search(c)
  if not match:
    return c
  word = c[:match.start()]
  tone = c[match.start():]
  return f'{word}<sup>{tone}</sup>'


def morphemeToRuby(m: Morpheme) -> str:
  if m['hidden']:
    return ''
  if len(m['cantoDefinitions']) == 0 and len(m['cantoPinyins']) == 0:
    return m['hanzi']

  pinyins = set(p for p in m['pinyins'] if p)
  allCantos: set[str] = set()
  if len(pinyins):
    for d in m['cantoDefinitions']:
      if d['mandarin'] in pinyins:
        allCantos.add(d['cantonese'])
    for r in m['cantoPinyins']:
      if r['mandarin'] in pinyins:
        allCantos.add(r['cantonese'])
  else:
    for d in m['cantoDefinitions']:
      allCantos.add(d['cantonese'])
    for r in m['cantoPinyins']:
      allCantos.add(r['cantonese'])

  more = '' if len(allCantos) == 1 else '<sup>+</sup>'
  canto: str = min(allCantos, default='unknown')
  cantos = canto.split(' ')
  if len(cantos) == len(m['hanzi']):
    hanzis = iter(m['hanzi'])
    return "".join(
        f"<ruby>{h}<rt>{cantoneseToHtml(c)}{more}</rt></ruby>" for h, c in zip(hanzis, cantos))

  canto = canto.replace(' ', '')
  return f'<ruby>{m["hanzi"]}<rt>{canto}{more}</rt></ruby>'


ruby = "".join("".join(map(morphemeToRuby, line)) if line else '\n' for line in parsed)
print("# Readings as HTML")
print(ruby)
