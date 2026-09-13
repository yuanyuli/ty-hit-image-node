import json
from civitai_client import CivitaiClient, QueryParams, ApiError


class _Response:
    def __init__(self, body):
        self.body = body.encode('utf-8')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self.body if size < 0 else self.body[:size]

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

def test_search_uses_requested_sort(monkeypatch):
    captured = {}
    class Fake(CivitaiClient):
        def _request_json(self, url):
            captured["url"] = url
            return {"items": [], "metadata": {}}
    Fake().search(QueryParams(site="civitai.com", sort="Newest"))
    assert "sort=Newest" in captured["url"]

def test_search_falls_back_for_unknown_sort(monkeypatch):
    captured = {}
    class Fake(CivitaiClient):
        def _request_json(self, url):
            captured["url"] = url
            return {"items": [], "metadata": {}}
    Fake().search(QueryParams(site="civitai.com", sort="not-a-civitai-sort"))
    assert "sort=Most+Reactions" in captured["url"]

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


def test_page_metadata_keeps_workflow_when_positive_prompt_is_hidden(monkeypatch):
    html = '''<script>
      {"hasPositivePrompt":false,"meta":{"prompt":"{\\"nodes\\":[]}"},
       "workflow":{"nodes":[{"id":1,"type":"CLIPTextEncode","widgets_values":["cat"]}],"version":1}}
    </script>'''
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: _Response(html))

    result = CivitaiClient().page_metadata('civitai.com', 142564294)

    assert result['hasPositivePrompt'] is False
    assert 'prompt' not in result
    assert result['workflow']['nodes'][0]['type'] == 'CLIPTextEncode'


def test_page_metadata_returns_prompt_and_workflow_when_prompt_is_public(monkeypatch):
    html = '''<script>
      {"hasPositivePrompt":true,"meta":{"prompt":"a real prompt","negativePrompt":"bad"},
       "workflow":{"nodes":[],"version":1}}
    </script>'''
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: _Response(html))

    result = CivitaiClient().page_metadata('civitai.com', 123)

    assert result['hasPositivePrompt'] is True
    assert result['prompt'] == 'a real prompt'
    assert result['negativePrompt'] == 'bad'
    assert result['workflow']['version'] == 1


def test_page_metadata_ignores_workflow_key_inside_serialized_prompt(monkeypatch):
    html = '''<script>
      {"meta":{"prompt":"contains \\\"workflow\\\": {\\\"nodes\\\": []}"},
       "workflow":{"nodes":[{"id":9}],"version":2}}
    </script>'''
    monkeypatch.setattr('urllib.request.urlopen', lambda *args, **kwargs: _Response(html))

    result = CivitaiClient().page_metadata('civitai.com', 456)

    assert result['workflow']['nodes'][0]['id'] == 9
