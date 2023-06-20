from collections.abc import Generator
from contextlib import AbstractContextManager
from typing import Any, Self, TypedDict

from attrs import define, field
from httpx import URL, Client

JSONDict = dict[str, Any]


class PageMeta(TypedDict):
    size: int
    offset: int
    limit: int


class ResponseJSON(TypedDict):
    metadata: PageMeta
    result: list[JSONDict]


@define
class PaginatedResponse:
    client: "ExportClient"
    table: str
    page_meta: PageMeta
    items: list[JSONDict]

    @property
    def is_last_page(self):
        return self.page_meta["size"] < self.page_meta["limit"]

    @classmethod
    def from_json(
        cls, client: "ExportClient", table: str, resp_json: ResponseJSON
    ) -> Self:
        return cls(client, table, resp_json["metadata"], resp_json["result"])

    def __iter__(self) -> Generator[JSONDict, None, None]:
        yield from self.items

    def iter_all(self) -> Generator[JSONDict, None, None]:
        yield from self.items
        if self.is_last_page:
            return
        limit = self.page_meta["limit"]
        offset = self.page_meta["offset"] + limit
        nextpage = self.client._get_data_export(self.table, limit=limit, offset=offset)
        yield from nextpage.iter_all()


@define
class ExportClient(AbstractContextManager):
    base_url: URL = field(converter=URL)
    auth_token: str
    _cached_client: Client | None = None

    @property
    def _client(self) -> Client:
        if self._cached_client is None:
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {self.auth_token}",
            }
            self._cached_client = Client(headers=headers)
        return self._cached_client

    def close(self):
        if self._cached_client:
            self._cached_client.close()
            self._cached_client = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_faqmatches(self, **kw) -> PaginatedResponse:
        return self._get_data_export("faqmatches", **kw)

    def _get_data_export(
        self, table: str, limit: int = 1000, offset: int = 0
    ) -> PaginatedResponse:
        params = {"limit": limit, "offset": offset}
        resp = self._client.get(self.base_url.join(table), params=params)
        resp.raise_for_status()
        return PaginatedResponse.from_json(self, table, resp.json())
