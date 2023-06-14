import json
from importlib import resources

import pytest

from aaq_sync.data_models import FAQModel
from aaq_sync.sync import remove_existing


def read_test_data(path: str) -> str:
    return (resources.files(__package__) / "test_data" / path).read_text()


def test_remove_existing():
    """
    Existing items are filtered out. Existing items with different values throw
    an exception.
    """
    faq_dicts = json.loads(read_test_data("two_faqs.json"))["faqs"]
    [faq1e, faq2e] = [FAQModel.from_json(faqd) for faqd in faq_dicts]
    [faq1n, faq2n] = [FAQModel.from_json(faqd) for faqd in faq_dicts]

    # If either input list is empty, the output is always the value of new.
    assert list(remove_existing([], [])) == []
    assert list(remove_existing([faq1e, faq2e], [])) == []
    assert list(remove_existing([], [faq1n, faq2n])) == [faq1n, faq2n]

    # Any existing values that are equal to their new equivalents are excluded
    # from the output.
    assert list(remove_existing([faq1e], [faq1n, faq2n])) == [faq2n]
    assert list(remove_existing([faq2e], [faq1n, faq2n])) == [faq1n]
    assert list(remove_existing([faq2e, faq1e], [faq1n, faq2n])) == []

    # If a new value isn't equal to an existing counterpart, we get an error.
    faq2n.faq_title = "New title"
    with pytest.raises(ValueError, match=r"already exists with different value"):
        list(remove_existing([faq2e], [faq1n, faq2n]))
