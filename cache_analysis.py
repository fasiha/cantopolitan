from contextlib import contextmanager
from chinese import ChineseAnalyzer  # type: ignore
import os.path
import typing
import pickle

ChineseAnalyzerResult = typing.Any


def resultsDump(results: dict[str, ChineseAnalyzerResult], fid: typing.BinaryIO):
  "Like JSON/pickle `dump`, serialize a dict of text->analyzer results to disk"
  # `ChineseAnalyzerResult`s include a pointer to the parent `ChineseAnalyzer`
  # object, which includes large dictionary objects, so pickle expands a small
  # result into 16 MB.  We overwrite this `__parent` slot so these results
  # objects are lightweight, then add them back to the input objects.
  # https://github.com/morinokami/chinese/blob/3f80ec36a4c4fa0b431626ae778d72ef28ebfa64/src/chinese/api.py#L44-L47
  parents = []
  for r in results.values():
    parents.append(r._ChineseAnalyzerResult__parent)
    r._ChineseAnalyzerResult__parent = None

  pickle.dump(results, fid)

  for result, parent in zip(results.values(), parents):
    result._ChineseAnalyzerResult__parent = parent


def resultsLoad(fid: typing.BinaryIO, analyzer: ChineseAnalyzer):
  "Like JSON/pickle `load`, deserialize a `dict` of analyzed results from disk"
  # As mentioned above, the pickled ChineseAnalyzerResult objects are missing
  # their `__parent` members. As part of the hydration, set `analyzer` as each
  # object's parent.
  results: dict[str, ChineseAnalyzerResult] = pickle.load(fid)
  for result in results.values():
    result._ChineseAnalyzerResult__parent = analyzer
  return results


@contextmanager
def cache_analysis(cache_filename: str, analyzer: ChineseAnalyzer):
  """Automatically cache Chinese analyzer results

  Usage:

  >>> from chinese import ChineseAnalyzer
  >>> analyzer = ChineseAnalyzer()
  >>> with cache_analysis("cache.pickle", analyzer) as cache:
  >>>   for line in sys.stdin.readlines():
  >>>     result = cache[line] if line in cache else analyzer.parse(line)
  >>>     cache[line] = result
  >>>     result.pprint()
  This manages the cache (a dict mapping text to Chinese analyzer results)
  inside the body. Even if an exception is raised in the body, or the program
  exits, the cache will be saved to disk.
  """
  cache: dict[str, ChineseAnalyzerResult] = dict()

  # load the cache
  if os.path.isfile(cache_filename):
    with open(cache_filename, 'rb') as fid:
      cache = resultsLoad(fid, analyzer)

  try:
    # yield the cache to the outer program
    yield cache

  finally:
    # dump the cache back to disk
    with open(cache_filename, 'wb') as fid:
      resultsDump(cache, fid)
