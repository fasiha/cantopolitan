# Cantopolitan

Add Cantonese readings to text.

## Setup

From https://cantonese.org/download.html download and unzip
1. "The latest version of CC-Canto", which this repo assumes is `cccanto-webdist.txt`, and
2. "The latest version of our Cantonese readings for CC-CEDICT", which this repo assumes is `cccedict-canto-readings-150923.txt`.

Then, after making sure you have [Git](https://git-scm.com) and [Python](https://www.python.org/downloads/) installed, open your command prompt, then run
1. `git clone https://github.com/fasiha/cantopolitan.git` to clone a copy of this repo from GitHub to your disk;
2. `cd cantopolitan` to change into the cloned directory;
3. `python -m pip install -r requirements.txt` to ask pip (the Python package manager) to install the upstream dependencies.

## Run

`main.py` reads input from `stdin` (see [this](https://stackoverflow.com/q/8980520) reference for a quick tutorial on `stdin`, `stdout`, etc.). You can do something like this:
```
echo 大香港精神 | python main.py
```
or
```
python main.py < MY_CANTONESE_TEXT_FILE.txt
```
and this Python code will spit out a lot of text about the input, including dictionary hits via Jieba/CC-CEDICT and via CC-Canto, and pronunciation. This output is *very messy* sorry in advance.
