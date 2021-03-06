# Cantopolitan

Add Cantonese readings to text.

## Setup

From https://cantonese.org/download.html download and unzip
1. "The latest version of CC-Canto", which this repo assumes is `cccanto-webdist.txt`, and
2. "The latest version of our Cantonese readings for CC-CEDICT", which this repo assumes is `cccedict-canto-readings-150923.txt`.

Next, from https://www.mdbg.net/chinese/dictionary?page=cc-cedict download and unzip
1. "cedict_1_0_ts_utf-8_mdbg.zip - CC-CEDICT", which should yield a text file called `cedict_ts.u8`.

Then, after making sure you have [Git](https://git-scm.com) and [Python](https://www.python.org/downloads/) installed, open your command prompt, then run
1. `git clone https://github.com/fasiha/cantopolitan.git` to clone a copy of this repo from GitHub to your disk;
2. `cd cantopolitan` to change into the cloned directory;
3. `python -m pip install -r requirements.txt` to ask pip (the Python package manager) to install the upstream dependencies.

## Run

`parse.py` reads input from `stdin` (see [this](https://stackoverflow.com/q/8980520) reference for a quick tutorial on `stdin`, `stdout`, etc.), and prints out a JSON file that you can redirect to a file. You can do something like this:
```
echo 大香港精神 | python parse.py > out.json
```
or
```
python parse.py < MY_CANTONESE_TEXT_FILE.txt > out.json
```
The JSON includes various things like dictionary hits via Jieba/CC-CEDICT and via CC-Canto, and pronunciation.

Then you can render this JSON to some nice Markdown with `parsed_to_md.py` which reads JSON from `stdin` and outputs Markdown to `stdout`. One way to invoke it is:
```
python parsed_to_md.py < out.json > out.md
```

We also offer a web server that will eventually allow you to edit the automatically-inferred definitions. Start that (macOS and Linux users can do this; Windows users, please [adjust](https://flask.palletsprojects.com/en/2.0.x/quickstart/)) with:
```
FLASK_APP=editor_server.py FLASK_ENV=development flask run
```
It expects a JSON file called `out.json` to exist and serves it to http://127.0.0.1:5000.