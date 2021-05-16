import typing
import json
import os.path

CantoDict = typing.Dict[str, typing.List[typing.Tuple[str, str, typing.List[str]]]]


def init(file: str, jsonfile: typing.Optional[str] = None) -> CantoDict:
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
      mandarin = mandarin[1:].strip()  # drop initial `[`
      cantonese = cantonese[:-1]  # drop final `}`

      glosses = glosses.split('#', 1)[0]  # drop trailing comments
      glosses = [g.strip() for g in glosses.split('/') if len(g) > 0]

      result = (mandarin, cantonese, glosses)
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
