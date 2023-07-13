import json
from importlib import resources

import pytest
from httpx import URL, HTTPStatusError

from aaq_sync.data_export_client import ExportClient
from aaq_sync.data_models import FAQModel

from .fake_data_export import FakeDataExport


@pytest.fixture()
def fake_data_export(httpx_mock):
    return FakeDataExport(URL("https://127.0.0.100:1234/"), httpx_mock)


def read_test_data(path: str) -> str:
    return (resources.files(__package__) / "test_data" / path).read_text()


def test_export_client_faqmatches(fake_data_export):
    """
    The client fetches all faq items at once if they fit in a single page.
    """
    [faq1, faq2] = json.loads(read_test_data("two_faqs.json"))["result"]

    with ExportClient(fake_data_export.base_url, "token") as ec:
        empty = ec.get_faqmatches()
        assert empty.page_meta["size"] == 0
        assert empty.items == []

        fake_data_export.faqmatches.append(faq1)
        one = ec.get_faqmatches()
        assert one.page_meta["size"] == 1
        assert one.items == [faq1]

        fake_data_export.faqmatches.append(faq2)
        two = ec.get_faqmatches()
        assert two.page_meta["size"] == 2
        assert two.items == [faq1, faq2]


def test_export_client_faqmatches_paginated(fake_data_export):
    """
    The client fetches a page at a time for the given limit and offset.
    """
    [faq1, faq2] = json.loads(read_test_data("two_faqs.json"))["result"]
    fake_data_export.faqmatches.extend([faq1, faq2])

    with ExportClient(fake_data_export.base_url, "token") as ec:
        p1 = ec.get_faqmatches(limit=1)
        assert p1.page_meta == {"size": 1, "limit": 1, "offset": 0}
        assert not p1.is_last_page
        assert p1.items == [faq1]

        p2 = ec.get_faqmatches(limit=1, offset=1)
        assert p2.page_meta == {"size": 1, "limit": 1, "offset": 1}
        assert not p2.is_last_page
        assert p2.items == [faq2]

        p3 = ec.get_faqmatches(limit=1, offset=2)
        assert p3.page_meta == {"size": 0, "limit": 1, "offset": 2}
        assert p3.is_last_page
        assert p3.items == []


def test_export_client_faqmatches_iter_page(fake_data_export):
    """
    A paginated response is an iterable over its own items.
    """
    [faq1, faq2] = json.loads(read_test_data("two_faqs.json"))["result"]
    fake_data_export.faqmatches.extend([faq1, faq2])

    with ExportClient(fake_data_export.base_url, "token") as ec:
        page = ec.get_faqmatches()
        assert list(iter(page)) == [faq1, faq2]


def test_export_client_faqmatches_iter_all(fake_data_export):
    """
    A paginated response can iterate over all items from itself and any future
    pages.
    """
    [faq1, faq2] = json.loads(read_test_data("two_faqs.json"))["result"]
    fake_data_export.faqmatches.extend([faq1, faq2])

    with ExportClient(fake_data_export.base_url, "token") as ec:
        page = ec.get_faqmatches(limit=1)
        assert list(iter(page)) == [faq1]
        assert list(page.iter_all()) == [faq1, faq2]


def test_export_client_auth(fake_data_export):
    """
    The client properly sends the given authentication token.
    """
    fake_data_export.token = "goodtoken"  # noqa: S105 (Not a real token.)
    with ExportClient(fake_data_export.base_url, "goodtoken") as ec:
        assert ec.get_faqmatches().items == []

    with ExportClient(fake_data_export.base_url, "badtoken") as ec:
        with pytest.raises(HTTPStatusError) as errinfo:
            ec.get_faqmatches()
        assert errinfo.value.response.status_code == 401


def test_export_client_models(fake_data_export):
    """
    Given a model class, the client fetches all items as instances of that
    model.
    """
    [faq1, faq2] = json.loads(read_test_data("two_faqs.json"))["result"]
    [faqm1, faqm2] = [FAQModel.from_json(faq) for faq in [faq1, faq2]]

    with ExportClient(fake_data_export.base_url, "token") as ec:
        empty = list(ec.get_model_items(FAQModel))
        assert empty == []

        fake_data_export.faqmatches.append(faq1)
        one = list(ec.get_model_items(FAQModel))
        assert one == [faqm1]

        fake_data_export.faqmatches.append(faq2)
        two = list(ec.get_model_items(FAQModel))
        assert two == [faqm1, faqm2]
