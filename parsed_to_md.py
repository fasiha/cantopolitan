import sys
import json
from parse import morphemeToBulletedDefs, morphemeToRuby, Morpheme
from partition_by import partitionBy

if __name__ == '__main__':
  morphemes: list[Morpheme] = json.load(sys.stdin)
  ruby = "".join(map(morphemeToRuby, morphemes))
  print("# Readings as HTML")
  print(ruby)

  print("# Morphemes")

  morphemesIter = iter(morphemes)
  for line in partitionBy(lambda m: m['hanzi'] == '\n', morphemesIter):
    text = "".join(m['hanzi'] for m in line if not m['hidden'])
    if len(text.strip()) == 0:
      continue
    print(f"## {text}")
    ruby = "".join(map(morphemeToRuby, line))
    print(f'### {ruby}')
    for m in line:
      bullets = morphemeToBulletedDefs(m)
      if len(bullets):
        print(bullets)
    print(json.dumps(line, ensure_ascii=False))
