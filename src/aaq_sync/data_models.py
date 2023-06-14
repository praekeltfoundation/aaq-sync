from datetime import datetime
from typing import Any, Self, TypeVar

from sqlalchemy import ARRAY, ColumnElement, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

T = TypeVar("T")


def _translate_json_field(col: ColumnElement, value: T) -> T | datetime | None:
    """
    Translate the JSON representation of a field to a db-friendly form and do
    basic type validation.
    """
    # col.type.python_type may raise NotImplementedError (when using
    # TypeDecorator, for example) but nothing in our existing models does that.
    col_pyt = col.type.python_type
    match value:
        case int(v) if col_pyt is datetime:
            # Timestamps are represented as milliseconds since the unix epoch.
            return datetime.utcfromtimestamp(v / 1000)
        case "None" if col.nullable and col_pyt is not str:
            # NULL values are apparently represented as the string "None".
            return None
        case _ if not isinstance(value, col_pyt):
            [vtype, ctype] = [t.__name__ for t in [type(value), col_pyt]]
            raise TypeError(f"{col.name} has type {vtype}, expected {ctype}")
    # Everything else is already in an appropriate form.
    return value


class Base(DeclarativeBase):
    type_annotation_map = {
        list[str]: ARRAY(String),
        list[float]: ARRAY(Float),
    }

    @classmethod
    def from_json(cls, json_dict: dict[str, Any]) -> Self:
        """
        Perform any translations or corrections necessary on the JSON data
        before instantiating this model.

        TODO: Better validation. Specifically, it would be nice to get all the
            validation errors at once instead of failing on the first.
        """
        json_fixed = {
            c.name: _translate_json_field(c, json_dict[c.name])
            for c in cls.__table__.columns
        }
        extra_keys = json_dict.keys() - json_fixed.keys()
        if extra_keys:
            keys = ", ".join(sorted(extra_keys))
            raise ValueError(f"Extra keys in JSON for {cls.__tablename__}: {keys}")
        return cls(**json_fixed)


class FAQModel(Base):
    """
    SQLAlchemy data model for FAQ

    (Copied from aaq_admin_template and translated to modern SQLAlchemy.)
    """

    __tablename__ = "faqmatches"

    faq_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    faq_added_utc: Mapped[datetime]
    faq_updated_utc: Mapped[datetime]
    faq_author: Mapped[str]
    faq_title: Mapped[str]
    faq_content_to_send: Mapped[str]
    faq_tags: Mapped[list[str] | None]
    faq_questions: Mapped[list[str]]
    faq_contexts: Mapped[list[str] | None]
    faq_thresholds: Mapped[list[float] | None]
    faq_weight: Mapped[int]
