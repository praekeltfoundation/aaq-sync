import click
from httpx import URL as HttpURL
from sqlalchemy import URL as DbURL
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url as make_db_url
from sqlalchemy.orm import Session

from .data_export_client import ExportClient
from .data_models import Base, get_models
from .sync import sync_model_items

MODEL_MAPPING = {m.__tablename__: m for m in get_models()}


class OptMixin:
    @classmethod
    def option(cls, *param_decls, **kw):
        kw.setdefault("required", True)
        kw.setdefault("type", cls())
        return click.option(*param_decls, **kw)


class DbURLParam(click.ParamType, OptMixin):
    name = "db_url"

    def convert(self, value, param, ctx):
        url = make_db_url(value)
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        return url


class HttpURLParam(click.ParamType, OptMixin):
    name = "http_url"

    def convert(self, value, param, ctx):
        return HttpURL(value)


class TableChoiceParam(click.Choice, OptMixin):
    name = "table"
    envvar_list_splitter = ","

    def __init__(self):
        super().__init__(choices=sorted(MODEL_MAPPING.keys()))

    def convert(self, value, param, ctx):
        return MODEL_MAPPING[super().convert(value, param, ctx)]


@click.command(context_settings={"auto_envvar_prefix": "AAQ_SYNC"})
@DbURLParam.option("--db-url", help="Database URL.")
@HttpURLParam.option("--export-url", help="Data export API URL.")
@click.option("--export-token", type=str, required=True, help="Export API auth token.")
@TableChoiceParam.option(
    "tables", "--table", multiple=True, help="Table to sync. (Multiple allowed.)"
)
def aaq_sync(
    db_url: DbURL,
    export_url: HttpURL,
    export_token: str,
    tables: list[type[Base]],
):
    """
    Sync one or more AAQ tables from the given data export API endpoint to the
    given database.
    """
    dbengine = create_engine(db_url, echo=False)
    with (
        Session(dbengine) as session,
        ExportClient(export_url, export_token) as exporter,
    ):
        for table in tables:
            click.echo(f"Syncing {table.__tablename__} ...")
            synced = sync_model_items(table, exporter, session)
            click.echo(f"Synced {len(synced)} {table.__tablename__} items.")
