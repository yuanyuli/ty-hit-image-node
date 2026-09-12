import json
from civitai_client import CivitaiClient, QueryParams, ApiError

def test_search_respects_count_and_parses_items():
    class Fake(CivitaiClient):
        def _request_json(self, url):
            return {"items": [{"id": 1, "type": "image"}, {"id": 2, "type": "image"}], "metadata": {"nextCursor": "same"}}
    result = Fake().search(QueryParams(site="civitai.com", count=1))
    assert [x["id"] for x in result.items] == [1]

def test_search_sfw_excludes_nsfw(monkeypatch):
    captured = {}
    class Fake(CivitaiClient):
        def _request_json(self, url):
            captured["url"] = url
            return {"items": [], "metadata": {}}
    Fake().search(QueryParams(site="civitai.com", sfw=True))
    assert "nsfw=false" in captured["url"]

def test_status_codes_are_readable():
    class Fake(CivitaiClient):
        def _request_json(self, url):
            raise ApiError(403, "需要授权或内容不可见")
    try:
        Fake().search(QueryParams(site="civitai.com", count=1))
    except ApiError as e:
        assert e.status == 403 and "授权" in str(e)
    else:
        assert False
