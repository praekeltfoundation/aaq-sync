import pytest

from aaq_sync.itertools import IteratorWithFinishedCheck


def test_iwfc_finished_empty():
    """
    If the IteratorWithFinishedCheck is empty, it's finished.
    """
    empty: IteratorWithFinishedCheck[None] = IteratorWithFinishedCheck([])

    assert empty.finished is True
    assert list(empty) == []


def test_iwfc_finished_non_empty():
    """
    If the IteratorWithFinishedCheck isn't empty, it's only finished when there
    are no more items.
    """
    one: IteratorWithFinishedCheck[int] = IteratorWithFinishedCheck([1])

    assert one.finished is False
    assert next(one) == 1
    assert one.finished is True

    three: IteratorWithFinishedCheck[int] = IteratorWithFinishedCheck([1, 2, 3])

    assert three.finished is False
    assert next(three) == 1
    assert three.finished is False
    assert list(three) == [2, 3]  # The remaining items
    assert three.finished is True


def test_iwfc_peek_next():
    """
    If the IteratorWithFinishedCheck isn't finished, .peek_next() will return
    the next item without consuming it. Otherwise it raises StopIteration.
    """
    three: IteratorWithFinishedCheck[int] = IteratorWithFinishedCheck([1, 2, 3])

    assert three.peek_next() == 1
    assert next(three) == 1
    assert three.peek_next() == 2
    assert list(three) == [2, 3]  # The remaining items
    # We're finished, so there's nothing left to peek at.
    with pytest.raises(StopIteration):
        three.peek_next()
