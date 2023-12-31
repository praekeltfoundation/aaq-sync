import json
from dataclasses import asdict

import pytest
from httpx import URL

from aaq_sync.data_export_client import ExportClient
from aaq_sync.data_models import Base, FAQModel
from aaq_sync.sync import fetch_existing, filter_existing, store_new, sync_model_items

from .fake_data_export import FakeDataExport
from .helpers import Database, read_test_data


@pytest.fixture()
def db(dbengine):
    Base.metadata.create_all(dbengine)
    return Database(dbengine)


@pytest.fixture()
def fake_data_export(httpx_mock):
    return FakeDataExport(URL("https://127.0.0.100:1234/"), httpx_mock)


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


def test_fetch_existing(db):
    """
    Existing items are fetched from the db.
    """
    faqs = db.faq_json_to_db("two_faqs.json")

    with db.session() as session:
        [faq1, faq2] = list(fetch_existing(FAQModel, session))
    assert [asdict(faq1), asdict(faq2)] == faqs


def test_store_new(db):
    """
    New items are stored in the db.
    """
    [faq1d, faq2d] = json.loads(read_test_data("two_faqs.json"))["result"]

    # Store nothing.
    with db.session() as session:
        assert store_new([], session) == []
        session.commit()
    assert db.fetch_faqs() == []

    # Store a new item.
    faq1 = FAQModel.from_json(faq1d)
    with db.session() as session:
        assert store_new([faq1], session) == [faq1]
        session.commit()
    assert db.fetch_faqs() == [faq1]

    # Store an old and a new item.
    faq2 = FAQModel.from_json(faq2d)
    with db.session() as session:
        assert store_new([faq1, faq2], session) == [faq2]
        session.commit()
    assert db.fetch_faqs() == [faq1, faq2]


def test_sync_model_items(fake_data_export, db):
    """
    New items from the export API are stored in the db.
    """
    [faq1d, faq2d] = json.loads(read_test_data("two_faqs.json"))["result"]

    with ExportClient(fake_data_export.base_url, "token") as ec:
        # Sync nothing.
        with db.session() as session:
            assert sync_model_items(FAQModel, ec, session) == []
        assert db.fetch_faqs() == []

        # Sync a new item.
        fake_data_export.faqmatches.append(faq1d)
        faq1 = FAQModel.from_json(faq1d)
        with db.session() as session:
            assert sync_model_items(FAQModel, ec, session) == [faq1]
        assert db.fetch_faqs() == [faq1]

        # Sync an old and a new item.
        fake_data_export.faqmatches.append(faq2d)
        faq2 = FAQModel.from_json(faq2d)
        with db.session() as session:
            assert sync_model_items(FAQModel, ec, session) == [faq2]
        assert db.fetch_faqs() == [faq1, faq2]
