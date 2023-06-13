import os

import pytest
from pytest_postgresql import factories
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

if "USE_EXISTING_PG" in os.environ:
    pg_fixture = factories.postgresql("postgresql_noproc")
else:
    pg_fixture = factories.postgresql("postgresql_proc")


@pytest.fixture()
def dbengine(pg_fixture):
    i = pg_fixture.info
    creds = f"{i.user}:{i.password}"
    url = f"postgresql+psycopg://{creds}@{i.host}:{i.port}/{i.dbname}"
    return create_engine(url, echo=False, poolclass=NullPool)
