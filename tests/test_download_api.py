from download_api import download_to_output
import pytest
from pathlib import Path

class _Response:
    def __init__(self, payload: bytes, headers=None):
        self.payload = payload
        self.offset = 0
        self.headers = headers or {}
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def getheader(self, name, default=None): return self.headers.get(name, default)
    def read(self, size=-1):
        if self.offset >= len(self.payload): return b''
        if size is None or size < 0: size = len(self.payload)
        chunk = self.payload[self.offset:self.offset + size]
        self.offset += len(chunk)
        return chunk

def test_download_rejects_untrusted_url(tmp_path):
    with pytest.raises(ValueError): download_to_output("https://evil.example/x.png", 1, tmp_path)

def test_download_rejects_path_traversal_id(tmp_path):
    with pytest.raises(ValueError): download_to_output("https://image.civitai.com/x.png", "../escape", tmp_path)

def test_download_enforces_response_size_and_cleans_temp_file(tmp_path, monkeypatch):
    import download_api
    monkeypatch.setattr(download_api, "safe_urlopen", lambda *args, **kwargs: _Response(b"12345", {"Content-Length": "5"}))
    with pytest.raises(ValueError, match="大小限制"):
        download_api.download_to_output("https://image.civitai.com/x.png", 1, tmp_path, max_bytes=4)
    assert not list((Path(tmp_path) / "ty-node").glob("*.tmp"))

def test_download_does_not_follow_redirects(tmp_path, monkeypatch):
    import download_api
    class RedirectResponse:
        headers = {}
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def geturl(self): return "https://evil.example/x.png"
    monkeypatch.setattr(download_api, "safe_urlopen", lambda *args, **kwargs: RedirectResponse())
    with pytest.raises(ValueError, match="重定向"):
        download_api.download_to_output("https://image.civitai.com/x.png", 1, tmp_path)
