from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.parse import urlparse

_HOSTS = {"civitai.com", "civitai.red", "image.civitai.com", "image.civitai.red"}

def allowed_url(url: str, site: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == site and site in _HOSTS

def redact_secrets(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if any(x in k.lower() for x in ("key", "token", "secret", "cookie")) else redact_secrets(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value

def safe_cache_path(root: Path, key: str, suffix: str = "") -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return root / f"{digest}{suffix}"
