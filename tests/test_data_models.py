import json
from datetime import datetime
from importlib import resources

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from aaq_sync.data_models import Base, FAQModel


@pytest.fixture()
def dbsession(dbengine):
    Base.metadata.create_all(dbengine)
    with Session(dbengine) as session:
        yield session


def read_test_data(path: str) -> str:
    return (resources.files(__package__) / "test_data" / path).read_text()


def fetch_faqs(dbsession: Session) -> list[FAQModel]:
    query = select(FAQModel).order_by(FAQModel.faq_id)
    return list(dbsession.scalars(query))


def test_faq(dbsession):
    """
    We can create FAQ entries and load them from the db.
    """
    assert fetch_faqs(dbsession) == []
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

    dbsession.add_all([faq1, faq2])
    dbsession.commit()

    assert fetch_faqs(dbsession) == [faq1, faq2]


def test_faq_from_json(dbsession):
    """
    When loading data from JSON, timestamps and "None" strings representing
    NULLs are translated into their db-friendly equivalents.
    """
    [faqd1, faqd2] = json.loads(read_test_data("two_faqs.json"))["faqs"]

    assert fetch_faqs(dbsession) == []

    faq1 = FAQModel.from_json(faqd1)
    faq2 = FAQModel.from_json(faqd2)
    dbsession.add_all([faq1, faq2])
    dbsession.commit()

    assert fetch_faqs(dbsession) == [faq1, faq2]
    # Millisecond timestamps are turned into datetimes.
    assert faqd1["faq_updated_utc"] == 1663239625854
    assert faq1.faq_updated_utc == datetime(2022, 9, 15, 11, 0, 25, 854000)
    # "None" strings representing NULLs are turned into Nones.
    assert faqd1["faq_contexts"] == "None"
    assert faq1.faq_contexts is None


def test_faq_from_json_validation(dbsession):
    """
    When loading data from JSON, various invalid inputs are detected.

    TODO: Better validation in the code under test.
    """
    faq_json = json.loads(read_test_data("two_faqs.json"))["faqs"][0]

    with pytest.raises(KeyError):
        FAQModel.from_json({})

    extra_match = r"Extra keys .* faqmatches: another, extra"
    with pytest.raises(ValueError, match=extra_match):
        FAQModel.from_json(faq_json | {"extra": "field", "another": 1})

    type_match = r"faq_id has type str, expected int"
    with pytest.raises(TypeError, match=type_match):
        FAQModel.from_json(faq_json | {"faq_id": "superego"})
