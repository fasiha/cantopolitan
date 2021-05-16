import typing
import json
import os.path

CantoReadings = typing.Dict[str, typing.List[typing.Tuple[str, str]]]
# hanzi (traditional) to list of (Mandarin pinyin, Cantonese pinyin)


def init(file: str, jsonfile: typing.Optional[str] = None) -> CantoReadings:
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
      mandarin = mandarin[1:].strip()  # drop initial `[`
      cantonese = cantonese[:-1]  # drop final `}`
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
