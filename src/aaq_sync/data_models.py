from sqlalchemy import ARRAY, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class FAQModel(Base):
    """
    SQLAlchemy data model for FAQ

    (Copied from aaq_admin_template and translated to plain SQLAlchemy.)
    """

    __tablename__ = "faqmatches"

    faq_id = Column(Integer, primary_key=True)
    faq_added_utc = Column(DateTime())
    faq_updated_utc = Column(DateTime())
    faq_author = Column(String())
    faq_title = Column(String())
    faq_content_to_send = Column(String())
    faq_tags = Column(ARRAY(String()))
    faq_questions = Column(ARRAY(String()), nullable=False)
    faq_contexts = Column(ARRAY(String()))
    faq_thresholds = Column(ARRAY(Float()))
    faq_weight = Column(Integer())
