import json
from dataclasses import asdict
from importlib import resources

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from aaq_sync.data_models import Base, FAQModel
from aaq_sync.sync import fetch_existing, filter_existing, store_new


@pytest.fixture()
def dbsession(dbengine):
    Base.metadata.create_all(dbengine)
    with Session(dbengine) as session:
        yield session


def read_test_data(path: str) -> str:
    return (resources.files(__package__) / "test_data" / path).read_text()


def faq_json_to_db(session: Session, path: str) -> list[dict]:
    faq_dicts = json.loads(read_test_data(path))["result"]
    faqs = [FAQModel.from_json(faqd) for faqd in faq_dicts]
    with session.begin(nested=True):
        session.add_all(faqs)
    return [asdict(m) for m in sorted(faqs, key=lambda m: m.pkey_value())]


def fetch_faqs(session: Session) -> list[FAQModel]:
    query = select(FAQModel).order_by(FAQModel.faq_id)
    return list(session.scalars(query))


def test_filter_existing():
    """
    Existing items are filtered out. Existing items with different values throw
    an exception.
    """
    faq_dicts = json.loads(read_test_data("two_faqs.json"))["result"]
    [faq1e, faq2e] = [FAQModel.from_json(faqd) for faqd in faq_dicts]
    [faq1n, faq2n] = [FAQModel.from_json(faqd) for faqd in faq_dicts]

    # If either input list is empty, the output is always the value of new.
    assert list(filter_existing([], [])) == []
    assert list(filter_existing([faq1e, faq2e], [])) == []
    assert list(filter_existing([], [faq1n, faq2n])) == [faq1n, faq2n]

    # Any existing values that are equal to their new equivalents are excluded
    # from the output.
    assert list(filter_existing([faq1e], [faq1n, faq2n])) == [faq2n]
    assert list(filter_existing([faq2e], [faq1n, faq2n])) == [faq1n]
    assert list(filter_existing([faq2e, faq1e], [faq1n, faq2n])) == []

    # If a new value isn't equal to an existing counterpart, we get an error.
    faq2n.faq_title = "New title"
    with pytest.raises(ValueError, match=r"already exists with different value"):
        list(filter_existing([faq2e], [faq1n, faq2n]))


def test_fetch_existing(dbsession):
    """
    Existing items are fetched from the db.
    """
    faqs = faq_json_to_db(dbsession, "two_faqs.json")

    [faq1, faq2] = list(fetch_existing(FAQModel, dbsession))
    assert [asdict(faq1), asdict(faq2)] == faqs


def test_store_new(dbsession):
    """
    New items are stored in the db.
    """
    [faq1d, faq2d] = json.loads(read_test_data("two_faqs.json"))["result"]

    # Store nothing.
    assert store_new([], dbsession) == []
    assert fetch_faqs(dbsession) == []

    # Store a new item.
    faq1 = FAQModel.from_json(faq1d)
    assert store_new([faq1], dbsession) == [faq1]
    assert fetch_faqs(dbsession) == [faq1]

    # Store an old and a new item.
    faq2 = FAQModel.from_json(faq2d)
    assert store_new([faq1, faq2], dbsession) == [faq2]
    assert fetch_faqs(dbsession) == [faq1, faq2]
