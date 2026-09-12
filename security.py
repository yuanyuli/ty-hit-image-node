from __future__ import annotations
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

_HOSTS = {"civitai.com", "civitai.red", "image.civitai.com", "image.civitai.red"}
MAX_REMOTE_BYTES = 50 * 1024 * 1024

def allowed_url(url: str, site: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.hostname == site and site in _HOSTS

def is_civitai_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and (parsed.hostname or "").lower() in _HOSTS

class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("不允许重定向到其他地址")

def safe_urlopen(request: Request, timeout: int = 30):
    return build_opener(_NoRedirectHandler).open(request, timeout=timeout)

def read_limited(response, max_bytes: int = MAX_REMOTE_BYTES) -> bytes:
    raw_length = response.headers.get("Content-Length") if getattr(response, "headers", None) else None
    if raw_length:
        try:
            if int(raw_length) > max_bytes:
                raise ValueError(f"响应超过大小限制（{max_bytes} 字节）")
        except ValueError as exc:
            if "大小限制" in str(exc):
                raise
    chunks, total = [], 0
    while True:
        chunk = response.read(min(1024 * 1024, max_bytes - total + 1))
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise ValueError(f"响应超过大小限制（{max_bytes} 字节）")
        chunks.append(chunk)
    return b"".join(chunks)

def redact_secrets(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if any(x in k.lower() for x in ("key", "token", "secret", "cookie")) else redact_secrets(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_secrets(v) for v in value]
    return value

def safe_cache_path(root: Path, key: str, suffix: str = "") -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return root / f"{digest}{suffix}"
