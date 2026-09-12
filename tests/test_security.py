from pathlib import Path
import pytest
from security import allowed_url, redact_secrets, safe_cache_path, is_civitai_url

def test_allows_only_selected_https_hosts():
    assert allowed_url("https://civitai.com/api/v1/images", "civitai.com")
    assert allowed_url("https://civitai.red/api/v1/images", "civitai.red")
    assert not allowed_url("http://civitai.com/api/v1/images", "civitai.com")
    assert not allowed_url("https://evil.example/api", "civitai.com")

def test_civitai_url_allowlist_rejects_non_https_and_subdomains():
    assert is_civitai_url("https://image.civitai.com/a.png")
    assert not is_civitai_url("http://image.civitai.com/a.png")
    assert not is_civitai_url("https://image.civitai.com.evil.example/a.png")

def test_redacts_secret_fields_recursively():
    value = redact_secrets({"api_key": "secret", "nested": [{"token": "abc"}], "x": 1})
    assert value == {"api_key": "[REDACTED]", "nested": [{"token": "[REDACTED]"}], "x": 1}

def test_cache_path_uses_hash_and_rejects_traversal():
    p = safe_cache_path(Path("cache"), "query/key", ".json")
    assert p.parent == Path("cache")
    assert p.suffix == ".json"
    assert ".." not in p.name
