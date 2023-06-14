from collections.abc import Collection, Generator
from dataclasses import asdict
from typing import TypeVar

from .data_models import Base

TBase = TypeVar("TBase", bound=Base)


def remove_existing(
    existing_items: Collection[TBase],
    new_items: Collection[TBase],
) -> Generator[Base, None, None]:
    """
    Filter existing items out of the new items collection. If any existing item
    doesn't have the same value as a corresponding new item, raise an
    exception.
    """
    if len(existing_items) == 0 or len(new_items) == 0:
        yield from new_items
        return
    edict = {existing.pkey_value(): existing for existing in existing_items}
    for new in new_items:
        nkey = new.pkey_value()
        if (existing := edict.get(nkey)) is not None:
            # Compare just the data, not ORM state.
            if asdict(existing) != asdict(new):
                ostr = f"{type(new).__name__}{nkey}"
                raise ValueError(f"Object already exists with different value: {ostr}")
            # Skip existing objects that already match.
        else:
            yield new
