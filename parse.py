from chinese import ChineseAnalyzer
from readings import ReadingEntry, init as initReadings
from cccanto import CantoEntry, init as initDict
import itertools as it
import typing
import re
from cache_analysis import cache_analysis
from wordfill import fill as wordfill

readings = initReadings('cccedict-canto-readings-150923.txt')
cdict = initDict('cccanto-webdist.txt')
ANALYSIS_CACHE_FILE = 'analysis_cache.pickle'


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

  # Jieba's hits per token, so at least 1, maybe more; all maybe None
  pinyins: list[typing.Optional[str]]
  definitions: list[typing.Optional[list[str]]]  # inner list: separate sub-meanings

  cantoDefinitions: list[CantoEntry]  # matched by hanzi
  cantoPinyins: list[ReadingEntry]  # also matched by hanzi but for comparison to pinyins
  # N.B., len(cantoDefinitions) might be != len(cantoPinyins)!

  merged: bool  # should default to false if from Jieba; when we create a new morpheme from multiple ones, set this to true
  hidden: bool  # should default to false if from Jieba; when a merged morpheme overshadows a Jieba morpheme, hide the latter
  guessed: bool  # should default to false if from Jieba


def initMorpheme(hanzi: str,
                 cantoDefinitions=[],
                 cantoPinyins=[],
                 merged=False,
                 hidden=False,
                 guessed=False) -> Morpheme:
  return Morpheme(
      hanzi=hanzi,
      pinyins=[],
      definitions=[],
      cantoDefinitions=cantoDefinitions,
      cantoPinyins=cantoPinyins,
      merged=merged,
      hidden=hidden,
      guessed=guessed)


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


# There are going to be words where we didn't find Cantonese readings.
# Break down these morphemes into individual pieces and try to find dictionary entries for these.
# Prefer the longest dictionary hit. This is risky!
def guessMissingReadings(morphemes: list[Morpheme]):
  # Step 1: build a small dictionary of all sub-words (spanning morpheme boundaries)
  guessNotNeededPredicate: typing.Callable[[Morpheme], bool] = lambda m: bool(
      len(m['cantoDefinitions']) or len(m['cantoPinyins']) or m['hidden'] or 0 == len(m['hanzi'].
                                                                                      strip()))
  missing: set[str] = set()
  for i, morpheme in enumerate(morphemes):
    if guessNotNeededPredicate(morpheme):
      continue
    adjacent = list(it.takewhile(lambda m: not guessNotNeededPredicate(m), morphemes[i:]))
    for hanzi in allSubwords("".join(m['hanzi'] for m in adjacent)):
      if hanzi in missing:
        continue
      if hanzi in cdict or hanzi in readings:
        missing.add(hanzi)

  # Step 2: find the largest words to "fill" a morpheme
  i = 0
  while i < len(morphemes):
    morpheme = morphemes[i]
    if guessNotNeededPredicate(morpheme):
      i += 1
      continue
    found = [k for k in allSubwords(morpheme['hanzi']) if k in missing]
    mash = "".join(found)
    if not all(char in mash for char in morpheme['hanzi']):
      i += 1
      continue
    # we have a hit for all characters in hanzi. Fill in the "biggest" first, greedily
    pieces = wordfill(morpheme['hanzi'], found)

    morphemes[i]['hidden'] = True

    newMorphemes: list[Morpheme] = []
    for p in pieces:
      m = initMorpheme(p, guessed=True)
      if p in cdict:
        m['cantoDefinitions'] = cdict[p]
      if p in readings:
        m['cantoPinyins'] = readings[p]
      newMorphemes.append(m)

    morphemes[i:i] = newMorphemes

    i += len(newMorphemes) + 1


ChineseAnalyzerResult = typing.Any


def parseTextToMorphemes(line: str) -> list[Morpheme]:
  analyzer = ChineseAnalyzer()

  with cache_analysis(ANALYSIS_CACHE_FILE, analyzer) as cache:
    if line in cache:
      result = cache[line]
    else:
      result = analyzer.parse(line, traditional=True)
      cache[line] = result

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

      newMorpheme = initMorpheme(entries[0]['hanzi'], cantoDefinitions=entries, merged=True)

      morphemes.insert(startIdx, newMorpheme)
      break

    startIdx += (numAccumulated + 1)
    # skip all accumulated morphemes and the one we just inserted

  guessMissingReadings(morphemes)

  return morphemes


def cantoneseToHtml(c: str, prefix='', suffix='') -> str:
  num = re.compile('[0-9]$')
  match = num.search(c)
  if not match:
    return c
  word = c[:match.start()]
  tone = c[match.start():]
  return f'{prefix}{word}<sup>{tone}{suffix}</sup>'


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
  guess = '¿' if m['guessed'] else ''
  canto: str = min(allCantos, default='unknown')
  cantos = canto.split(' ')
  if len(cantos) == len(m['hanzi']):
    hanzis = iter(m['hanzi'])
    return "".join(f"<ruby>{h}<rt>{cantoneseToHtml(c, prefix=guess, suffix=more)}</rt></ruby>"
                   for h, c in zip(hanzis, cantos))

  canto = canto.replace(' ', '')
  return f'<ruby>{m["hanzi"]}<rt>{guess}{canto}{more}</rt></ruby>'


if __name__ == '__main__':
  import json
  import sys

  stdin = sys.stdin.read()
  morphemes = parseTextToMorphemes(stdin)
  print(json.dumps(morphemes))
