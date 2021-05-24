import typing

T = typing.TypeVar('T')


def partitionBy(f, v: typing.Iterator[T]):
  "https://clojuredocs.org/clojure.core/partition-by"
  try:
    x = next(v)
  except StopIteration:
    return []
  buffer: list[T] = [x]
  oldy = f(x)
  for x in v:
    y = f(x)
    if y != oldy:
      yield buffer
      buffer = []
    buffer.append(x)
    oldy = y
  yield buffer
