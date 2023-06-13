from datetime import datetime

from sqlalchemy import ARRAY, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {
        list[str]: ARRAY(String),
        list[float]: ARRAY(Float),
    }


class FAQModel(Base):
    """
    SQLAlchemy data model for FAQ

    (Copied from aaq_admin_template and translated to modern SQLAlchemy.)
    """

    __tablename__ = "faqmatches"

    faq_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faq_added_utc: Mapped[datetime]
    faq_updated_utc: Mapped[datetime | None]
    faq_author: Mapped[str]
    faq_title: Mapped[str]
    faq_content_to_send: Mapped[str]
    faq_tags: Mapped[list[str] | None]
    faq_questions: Mapped[list[str]]
    faq_contexts: Mapped[list[str] | None]
    faq_thresholds: Mapped[list[float] | None]
    faq_weight: Mapped[int]
