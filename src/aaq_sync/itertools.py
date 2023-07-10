from collections.abc import Iterable, Iterator
from typing import Generic, TypeVar

T = TypeVar("T")


class IteratorWithFinishedCheck(Generic[T]):
    """
    An iterator that knows if it's reached its end.
    """

    _iter: Iterator[T]
    _next_item: T
    _finished: bool = False

    @property
    def finished(self) -> bool:
        return self._finished

    def __init__(self, iterable: Iterable[T]):
        self._iter = iter(iterable)
        self._set_next()

    def __iter__(self):
        return self

    def __next__(self) -> T:
        if self._finished:
            raise StopIteration
        next_item = self._next_item
        self._set_next()
        return next_item

    def _set_next(self):
        try:
            self._next_item = next(self._iter)
        except StopIteration:
            self._finished = True

    def peek_next(self) -> T:
        if self.finished:
            raise StopIteration
        return self._next_item
