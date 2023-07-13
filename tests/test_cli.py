import json

import pytest
from click.testing import CliRunner
from httpx import URL

from aaq_sync.cli import aaq_sync
from aaq_sync.data_models import Base, FAQModel

from .fake_data_export import FakeDataExport
from .helpers import Database, read_test_data

OPTS_DB = ("--db-url", "postgresql://db.example.com:5432/testdb")
OPTS_EXPORT_URL = ("--export-url", "http://export.example.com")
OPTS_EXPORT_TOKEN = ("--export-token", "faketoken")
OPTS_EXPORT = (*OPTS_EXPORT_URL, *OPTS_EXPORT_TOKEN)
OPTS_TABLE = ("--table", "faqmatches")


@pytest.fixture()
def runner():
    """
    Fixture providing a CliRunner with an isolated filesystem.
    """
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


@pytest.fixture()
def db(dbengine):
    Base.metadata.create_all(dbengine)
    return Database(dbengine)


@pytest.fixture()
def fake_data_export(httpx_mock):
    return FakeDataExport(URL("https://127.0.0.100:1234/"), httpx_mock)


def test_missing_opts(runner):
    """
    All required options must be provided.
    """
    result = runner.invoke(aaq_sync, [*OPTS_EXPORT, *OPTS_TABLE])
    assert "Missing option '--db-url'" in result.output
    assert result.exit_code != 0

    result = runner.invoke(aaq_sync, [*OPTS_DB, *OPTS_EXPORT_TOKEN, *OPTS_TABLE])
    assert "Missing option '--export-url'" in result.output
    assert result.exit_code != 0

    result = runner.invoke(aaq_sync, [*OPTS_DB, *OPTS_EXPORT_URL, *OPTS_TABLE])
    assert "Missing option '--export-token'" in result.output
    assert result.exit_code != 0

    result = runner.invoke(aaq_sync, [*OPTS_DB, *OPTS_EXPORT])
    assert "Missing option '--table'" in result.output
    assert result.exit_code != 0


def test_sync_faqmatches(runner, fake_data_export, db):
    """
    All FAQ items are synced from the data export API to the db.
    """
    faqds = json.loads(read_test_data("two_faqs.json"))["result"]
    [faq1, faq2] = [FAQModel.from_json(faqd) for faqd in faqds]
    fake_data_export.faqmatches.extend(faqds)

    assert db.fetch_faqs() == []

    opts = [
        *("--db-url", db.engine.url),
        *("--export-url", fake_data_export.base_url),
        *("--export-token", "faketoken"),
        *("--table", "faqmatches"),
    ]

    result = runner.invoke(aaq_sync, opts)
    print(result.output)
    assert result.exit_code == 0
    assert db.fetch_faqs() == [faq1, faq2]


def test_sync_faqmatches_envvars(runner, fake_data_export, db, monkeypatch):
    """
    All config options can be provided through envvars.
    """
    faqds = json.loads(read_test_data("two_faqs.json"))["result"]
    [faq1, faq2] = [FAQModel.from_json(faqd) for faqd in faqds]
    fake_data_export.faqmatches.extend(faqds)

    assert db.fetch_faqs() == []

    monkeypatch.setenv("AAQ_SYNC_DB_URL", str(db.engine.url))
    monkeypatch.setenv("AAQ_SYNC_EXPORT_URL", str(fake_data_export.base_url))
    monkeypatch.setenv("AAQ_SYNC_EXPORT_TOKEN", "faketoken")
    monkeypatch.setenv("AAQ_SYNC_TABLES", "faqmatches")

    result = runner.invoke(aaq_sync, [])
    print(result.output)
    assert result.exit_code == 0
    assert db.fetch_faqs() == [faq1, faq2]
