from chinese import ChineseAnalyzer
from readings import init as initReadings
from cccanto import init as initDict
import itertools as it
import typing
import re
import sys

readings = initReadings('cccedict-canto-readings-150923.txt')
cdict = initDict('cccanto-webdist.txt')

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


parsed: list[list[Morpheme]] = []
for line in sys.stdin.readlines():
  if len(line) == 0:
    parsed.append([Morpheme(hanzi='', pinyin=None, canto=None)])
    continue

  print(f'## {line}')
  result = analyzer.parse(line, traditional=True)

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
    startIdx += numAccum

  print(morphemes)
  parsed.append(morphemes)

  for tokenIdx, token in enumerate(result.tokens()):
    print(f'### {token}')
    for hitIdx, hit in enumerate(result[token]):
      if len(result[token]) > 1:
        print(f"#### {hitIdx}")

      print(hit)
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
  canto: str = next(iter(m['canto']), '')
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
