import json
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import asdict
from importlib import resources

from attrs import define
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from aaq_sync.data_models import FAQModel


def read_test_data(path: str) -> str:
    return (resources.files(__package__) / "test_data" / path).read_text()


@define
class Database:
    engine: Engine

    @contextmanager
    def session(self, **kw) -> Generator[Session, None, None]:
        kw.setdefault("expire_on_commit", False)
        with Session(self.engine, **kw) as session:
            yield session

    def fetch_faqs(self) -> list[FAQModel]:
        query = select(FAQModel).order_by(FAQModel.faq_id)
        with self.session() as session:
            return list(session.scalars(query))

    def faq_json_to_db(self, path: str) -> list[dict]:
        faq_dicts = json.loads(read_test_data(path))["result"]
        faqs = [FAQModel.from_json(faqd) for faqd in faq_dicts]
        with self.session() as session:
            session.add_all(faqs)
            session.commit()
        return [asdict(m) for m in sorted(faqs, key=lambda m: m.pkey_value())]
