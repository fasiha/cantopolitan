from contextlib import contextmanager
from chinese import ChineseAnalyzer
import os.path
import typing
import pickle

ChineseAnalyzerResult = typing.Any


def resultsDump(results: dict[str, ChineseAnalyzerResult], fid: typing.BinaryIO):
  parents = []
  for r in results.values():
    parents.append(r._ChineseAnalyzerResult__parent)
    r._ChineseAnalyzerResult__parent = None

  pickle.dump(results, fid)

  for result, parent in zip(results.values(), parents):
    result._ChineseAnalyzerResult__parent = parent


def resultsLoad(fid: typing.BinaryIO, analyzer: ChineseAnalyzer):
  results: dict[str, ChineseAnalyzerResult] = pickle.load(fid)
  for result in results.values():
    result._ChineseAnalyzerResult__parent = analyzer
  return results


@contextmanager
def cache_analysis(cache_filename: str, analyzer: ChineseAnalyzer):
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
