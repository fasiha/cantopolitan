"""
CC-Canto ***readings*** data

Creates a dict corresponding to the Cantonese readings for CC-CEDICT made
available by [CC-Canto](https://cantonese.org/download.html).

This file has lines in the format
```
[traditional hanzi] [simplified hanzi] [Mandarin pinyin] {Cantonese pinyin}
```

The dict returned has type `CantoReadings` below: its keys are traditional
hanzi, and its values are lists of `(Mandarin pinyin, Cantonese pinyin)` tuples.
The pinyin tuples are in a *list* because the same hanzi can correspond to
multiple readings.

Caches the dict to JSON for faster loading.
"""

import typing
import json
import os.path

CantoReadings = dict[str, list[tuple[str, str]]]
# hanzi (traditional) to list of (Mandarin pinyin, Cantonese pinyin)


def init(file: str, jsonfile: typing.Optional[str] = None) -> CantoReadings:
  """Loads the CC-Canto readings file for CC-Edict

  Currently this file has format "cccedict-canto-readings-NUMBERS.txt". A path
  to such a file is needed for `file` argument. A JSON file will be saved to
  `jsonfile` (defaults to `file + '.json'`).
  """
  jsonfile = jsonfile or (file + '.json')

  if os.path.exists(jsonfile):
    return json.load(open(jsonfile, 'r'))

  d: CantoReadings = dict()
  with open(file, 'r') as fid:
    for line in fid.readlines():
      if line.startswith('#'):
        continue
      trad, _, readings = line.strip().split(" ", 2)
      mandarin, cantonese = readings.strip().split('] {')
      mandarin = mandarin.removeprefix('[')
      cantonese = cantonese.removesuffix('}')
      result = (mandarin, cantonese)
      if trad in d:
        d[trad].append(result)
      else:
        d[trad] = [result]
  with open(jsonfile, 'w') as fid:
    json.dump(d, fid)

  return d


if __name__ == '__main__':
  d = init('cccedict-canto-readings-150923.txt')
  res = d['精神']
  print(res)
  assert len(res) == 2, "two readings for 精神"
