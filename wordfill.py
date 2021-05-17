from typing import Collection


def fill(word: str, dictionary: Collection[str], alreadySorted: bool = False) -> list[str]:
  """Greedy longest word-filling

  Given a `word` and a `dictionary` of words in your language (not a Python
  dict), returns a list of entries from the `dictionary` that when joined
  together, equal `word`, and moreover, the *biggest* words are chosen. That is,
  you can `assert word == "".join(fill(word, dictionary))`.

  Raises when the `dictionary` cannot "cover" the `word`. Because the algorithm
  is greedy, and simple, we don't backtrack to try to find a different way to
  split the `word` that avoids dead-ends where the algorithm cannot advance
  further. Therefore, an exception being raised does not mean that the word
  can't be split with these dictionary entries, just that this simple algorithm
  couldn't do it.

  This will create a sorted copy of the `dictionary` unless `alreadySorted=True`
  is passed in.
  """
  return _worker(word, dictionary if alreadySorted else sorted(dictionary, key=len, reverse=True))


def _worker(s: str, dsort: Collection[str]):
  "Recursively split s"
  for word in dsort:
    if word in s:
      left, right = s.split(word, maxsplit=1)
      # use maxsplit to ensure only left/right instead of more than two chunks
      # if this word appears in the string multiple times to simplify the code
      # below, instead of dealing with interleaving `s`.

      ret: list[str] = []
      if len(left):
        ret.extend(_worker(left, dsort))
      ret.append(word)
      if len(right):
        ret.extend(_worker(right, dsort))
      return ret
  raise ValueError("dictionary must cover input")


if __name__ == '__main__':
  word = "barrybutton"
  expected = ["barry", "button"]

  myset = {"barry", "bar", "but", "ton", "button"}
  mylist = list(myset)
  mydict = {k: i**2 * (-1)**i for i, k in enumerate(mylist)}
  assert (fill(word, myset) == expected)
  assert (fill(word, mylist) == expected)
  assert (fill(word, mydict) == expected)
  print("Success!")
