import json
from datetime import datetime

import pytest

from aaq_sync.data_models import Base, FAQModel, get_models

from .helpers import Database, read_test_data


@pytest.fixture()
def db(dbengine):
    Base.metadata.create_all(dbengine)
    return Database(dbengine)


def test_get_models():
    """
    We can get a list of available models.
    """
    # NOTE: This needs to be updated for every model we add.
    assert get_models() == {FAQModel}


def test_faq(db):
    """
    We can create FAQ entries and load them from the db.
    """
    assert db.fetch_faqs() == []
    now = datetime.utcnow()

    faq1 = FAQModel(
        faq_added_utc=now,
        faq_updated_utc=now,
        faq_author="Author",
        faq_title="How to Ask a Question",
        faq_content_to_send="Politely.",
        faq_weight=42,
        faq_tags=["ask", "question"],
        faq_questions=["How do I ask a question?", "Huh?"],
        faq_thresholds=[0.4],
    )

    faq2 = FAQModel(
        faq_added_utc=now,
        faq_updated_utc=now,
        faq_author="Author",
        faq_title="How to Answer a Question",
        faq_content_to_send="Accurately.",
        faq_weight=42,
        faq_questions=["How do I answer a question?"],
    )

    with db.session() as session:
        session.add_all([faq1, faq2])
        session.commit()

    assert db.fetch_faqs() == [faq1, faq2]


def test_faq_from_json(db):
    """
    When loading data from JSON, timestamps are translated into their
    db-friendly equivalents.
    """
    [faqd1, faqd2] = json.loads(read_test_data("two_faqs.json"))["result"]

    assert db.fetch_faqs() == []

    faq1 = FAQModel.from_json(faqd1)
    faq2 = FAQModel.from_json(faqd2)
    with db.session() as session:
        session.add_all([faq1, faq2])
        session.commit()

    assert db.fetch_faqs() == [faq1, faq2]
    # Millisecond timestamps are turned into datetimes.
    assert faqd1["faq_updated_utc"] == 1663239625854
    assert faq1.faq_updated_utc == datetime(2022, 9, 15, 11, 0, 25, 854000)


def test_faq_from_json_validation():
    """
    When loading data from JSON, various invalid inputs are detected.

    TODO: Better validation in the code under test.
    """
    faq_json = json.loads(read_test_data("two_faqs.json"))["result"][0]

    with pytest.raises(KeyError):
        FAQModel.from_json({})

    extra_match = r"Extra keys .* faqmatches: another, extra"
    with pytest.raises(ValueError, match=extra_match):
        FAQModel.from_json(faq_json | {"extra": "field", "another": 1})

    type_match = r"faq_id has type str, expected int"
    with pytest.raises(TypeError, match=type_match):
        FAQModel.from_json(faq_json | {"faq_id": "superego"})
