from datetime import datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool

from aaq_sync.data_models import Base, FAQModel


@pytest.fixture()
def dbsession(postgresql):
    i = postgresql.info
    url = f"postgresql+psycopg://{i.user}:@{i.host}:{i.port}/{i.dbname}"
    engine = create_engine(url, echo=False, poolclass=NullPool)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def fetch_faqs(dbsession: Session) -> list[FAQModel]:
    query = select(FAQModel).order_by(FAQModel.faq_id)
    return list(dbsession.execute(query).scalars())


def test_faq(dbsession):
    """
    We can create an FAQ entry and load it from the db.
    """
    assert fetch_faqs(dbsession) == []
    now = datetime.utcnow()

    faq = FAQModel(
        faq_added_utc=now,
        faq_updated_utc=now,
        faq_author="Author",
        faq_title="How to Ask a Question",
        faq_content_to_send="Politely",
        faq_weight=42,
        faq_tags=["ask", "question"],
        faq_questions=["How do I ask a question?", "Huh?"],
        faq_contexts=[],
        faq_thresholds=[],
    )

    dbsession.add(faq)
    dbsession.commit()

    assert fetch_faqs(dbsession) == [faq]
