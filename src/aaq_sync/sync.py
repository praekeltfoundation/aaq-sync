from collections.abc import Generator, Iterable, Sequence
from dataclasses import asdict
from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from .data_models import Base

T = TypeVar("T")
# Note: `TGen` on its own is equivalent to `TGen[Any]`.
TGen = Generator[T, None, None]
TBase = TypeVar("TBase", bound=Base)


def filter_existing(olds: Iterable[TBase], news: Sequence[TBase]) -> TGen[TBase]:
    """
    Filter existing items out of the new items collection. If any existing item
    doesn't have the same value as a corresponding new item, raise an
    exception.
    """
    if len(news) == 0:
        return
    existing = {old.pkey_value(): old for old in olds}
    for new in news:
        nkey = new.pkey_value()
        if (old := existing.get(nkey)) is not None:
            # Compare just the data, not ORM state.
            if asdict(old) != asdict(new):
                ostr = f"{type(new).__name__}{nkey}"
                raise ValueError(f"Object already exists with different value: {ostr}")
            # Skip existing objects that already match.
        else:
            yield new


def fetch_existing(model: type[TBase], session: Session) -> Iterable[TBase]:
    """
    Fetch existing items from the database.
    """
    return session.scalars(select(model).order_by(*model.__table__.primary_key))


def store_new(news: Sequence[TBase], session: Session) -> Sequence[TBase]:
    """
    Store new items in the database.
    """
    if len(news) == 0:
        return []
    olds = fetch_existing(type(news[0]), session)
    stored: list[TBase] = []
    with session.begin(nested=True):
        for new in filter_existing(olds, news):
            session.add(new)
            stored.append(new)
    return stored
