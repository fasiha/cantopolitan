import json
from contextlib import contextmanager
from pypandoc import convert_text
from flask import Flask, send_from_directory
from parse import morphemeToBulletedDefs, morphemeToRuby, Morpheme
from partition_by import partitionBy

JSON_PATH = 'out.json'
PANDOC_FROM = 'markdown_github+hard_line_breaks+yaml_metadata_block+markdown_in_html_blocks+auto_identifiers'
PANDOC_EXTRA_ARGS = ['-s', '--metadata', 'pagetitle=Cantonese']


def pandoc(markdown: str) -> str:
  return convert_text(markdown, to='html5', format=PANDOC_FROM, extra_args=PANDOC_EXTRA_ARGS)


@contextmanager
def saved_morphemes(jsonpath: str):
  morphemes: list[Morpheme] = []
  # load morphemes
  with open(jsonpath, 'r') as fid:
    morphemes = json.load(fid)
  try:
    # yield morphemes to the outer program
    yield morphemes
  finally:
    # dump morphemes to disk
    with open(jsonpath, 'w') as fid:
      json.dump(morphemes, fid)


app = Flask(__name__)


@app.route('/perfectmotherfuckingwebsite.css')
def css():
  return send_from_directory(app.root_path, 'perfectmotherfuckingwebsite.css')


@app.route("/")
def hello_world():
  with open(JSON_PATH, 'r') as fid:
    morphemes: list[Morpheme] = json.load(fid)
  # markdown = "".join(map(morphemeToRuby, morphemes))

  markdownLines: list[str] = []
  morphemesIter = iter(morphemes)
  for line in partitionBy(lambda m: m['hanzi'] == '\n', morphemesIter):
    text = "".join(map(morphemeToRuby, line))
    if len(text.strip()) == 0:
      continue
    markdownLines.append(f'\n## {text}')
    defs = "\n".join(morphemeToBulletedDefs(m) for m in line)
    markdownLines.append(defs)
  markdown = "\n".join(markdownLines)

  return pandoc(markdown)
