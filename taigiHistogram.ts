/*
## Setup: first run
```
$ npm install esbuild
```
and download
https://github.com/g0v/moedict-data-twblg/blob/master/dict-twblg.json

## Build
```
$ ./node_modules/.bin/esbuild taigiHistogram.ts --bundle --platform=node
--outfile=taigiHistogram.js
```
(I think `npx` takes longer than `esbuild`! So I call directly from
node_modules)

## Run
```
$ node taigiHistogram.js
```
will output `taigi_histogram.json`.

This will be a list of tuples, the leading consonent/(vowel?) and a number
between 0 and 1 representing the fraction of morphemes with that leading sound.
*/

import {readFileSync, writeFileSync} from 'fs';
const example = [
  {
    'title': '袂伸捙',
    'heteronyms': [{
      'id': '6688',
      'trs': 'bē-tshun-tshia/buē-tshun-tshia',
      'synonyms': '袂翻捙',
      'definitions': [{
        'type': '熟',
        'def': '通常指經過言詞勸說之後，仍無法改變對方的態度或想法。',
        'example': [
          '￹佮伊講話，見講嘛講袂伸捙。￺Kah i kóng-uē, kiàn kóng mā kóng bē-tshun-tshia. ￻跟他說話，怎麼說都說不清楚。'
        ]
      }]
    }]
  },
  {
    'title': '袂使',
    'heteronyms': [{
      'id': '6666',
      'trs': 'bē-sái/buē-sái',
      'synonyms': '袂用得,袂使得',
      'definitions': [{
        'type': '副',
        'def': '不可以、使不得。',
        'example': [
          '￹你袂使佮伊出去𨑨迌！￺Lí bē-sái kah i tshut-khì tshit-thô! ￻你不可以和他出去玩！'
        ]
      }]
    }]
  },
];

function accentedLatinWords(s: string) {
  const m = s.match(/[\p{Script=Latin}\p{M}]+/gu)
  if (m) {
    return [...m].map(s => s.toLocaleLowerCase())
  }
  return [];
}

function count<T>(arr: T[]): Map<T, number> {
  const m: Map<T, number> = new Map();
  for (const x of arr) {
    m.set(x, (m.get(x) || 0) + 1);
  }
  return m;
}

function orderedCount<T>(arr: T[], asc = true): [T, number][] {
  const m = count(arr);
  const ret = [...m];
  const factor = asc ? 1 : -1;
  ret.sort(([_, a], [_2, b]) => (a - b) * factor);
  return ret;
}

const dict: typeof example =
    JSON.parse(readFileSync('dict-twblg.json', 'utf8'));

const examples =
    Array.from(new Set(dict.flatMap(
                               o => o.heteronyms.flatMap(
                                   o => o.definitions.flatMap(o => o.example)))
                           .filter(s => !!s)));

const words = examples.flatMap(accentedLatinWords);
const leading = words.flatMap(o => o.match(/^[^aeiou]+/gu)).filter(s => !!s);
const hist = orderedCount(leading, false);
for (const arr of hist) {
  arr[1] /= leading.length;
}
writeFileSync('taigi_histogram.json', JSON.stringify(hist, null, 1));
