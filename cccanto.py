"""
Full CC-Canto dictionary data

Loads the [CC-Canto](https://cantonese.org/download.html) dictionary ("The
latest version of CC-Canto …"). This is a text file whose lines have the
following format:
```
[traditional hanzi] [simplified hanzi] [Mandarin pinyin] {Cantonese pinyin} /English glosses/
```

The dictionary is returned in a dict whose type is given by `CantoDict` below.
The keys are hanzi, and values are a list of entries where each entry has
- Mandarin pinyin,
- Cantonese pinyin,
- English gloss, and
- the hanzi again.

A JSON copy of the returned dict will be saved for faster loading.
"""

import typing
import json
import os.path


class CantoEntry(typing.TypedDict):
  hanzi: str
  mandarin: str
  cantonese: str
  definition: str


Hanzi = str
CantoDict = dict[Hanzi, list[CantoEntry]]


def init(file: str, jsonfile: typing.Optional[str] = None) -> CantoDict:
  """Loads the CC-Canto dictionary

  `file` is assumed to point to a CC-Canto dictionary file (currently called
  "cccanto-webdist.txt").

  A JSON file of the returned dict will be saved in `jsonfile` (by default,
  `file + '.json'`).
  """
  jsonfile = jsonfile or (file + '.json')

  if os.path.exists(jsonfile):
    return json.load(open(jsonfile, 'r'))

  d: CantoDict = dict()
  with open(file, 'r') as fid:
    for line in fid.readlines():
      if line.startswith('#'):
        continue
      trad, _, rest = line.strip().split(" ", 2)
      readings, glosses = rest.split('/', 1)

      mandarin, cantonese = readings.strip().split('] {')
      mandarin = mandarin.removeprefix('[').strip()
      cantonese = cantonese.removesuffix('}')

      glosses = glosses.split('#', 1)[0]  # drop trailing comments
      glosses = glosses.strip().removesuffix('/')

      result = CantoEntry(hanzi=trad, mandarin=mandarin, cantonese=cantonese, definition=glosses)
      if trad in d:
        d[trad].append(result)
      else:
        d[trad] = [result]

  with open(jsonfile, 'w') as fid:
    json.dump(d, fid)

  return d


if __name__ == '__main__':
  d = init('cccanto-webdist.txt')
  print(d['一個二個'])
