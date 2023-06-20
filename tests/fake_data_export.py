from typing import Any

from attrs import define, field
from httpx import URL, Request, Response
from pytest_httpx import HTTPXMock

JSONDict = dict[str, Any]


@define
class FakeDataExport:
    base_url: URL
    mock: HTTPXMock
    token: str | None = None

    faqmatches: list[JSONDict] = field(factory=list)

    def __attrs_post_init__(self):
        self.mock.add_callback(self.handle_request)

    def handle_request(self, req: Request) -> Response:
        req_auth = req.headers["Authorization"]
        if self.token is not None and req_auth != f"Bearer {self.token}":
            body = {"error": "Authorization Failed!", "message": "Invalid Auth Token"}
            return Response(status_code=401, json=body)
        path = req.url.path[len(self.base_url.path) :]
        items = {
            "faqmatches": self.faqmatches,
        }[path]
        offset = int(req.url.params["offset"])
        limit = int(req.url.params["limit"])
        items = items[offset:][:limit]
        meta = {"size": len(items), "offset": offset, "limit": limit}
        return Response(status_code=200, json={"metadata": meta, "result": items})
