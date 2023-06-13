from datetime import datetime

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from aaq_sync.data_models import Base, FAQModel


@pytest.fixture()
def dbsession(dbengine):
    Base.metadata.create_all(dbengine)
    with Session(dbengine) as session:
        yield session


def fetch_faqs(dbsession: Session) -> list[FAQModel]:
    query = select(FAQModel).order_by(FAQModel.faq_id)
    return list(dbsession.execute(query).scalars())


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
        faq_author="Author",
        faq_title="How to Answer a Question",
        faq_content_to_send="Accurately.",
        faq_weight=42,
        faq_questions=["How do I answer a question?"],
    )

    dbsession.add(faq1)
    dbsession.add(faq2)
    dbsession.commit()

    assert fetch_faqs(dbsession) == [faq1, faq2]
