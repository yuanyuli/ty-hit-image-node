from pathlib import Path
from urllib.request import Request, urlopen
from security import is_civitai_url, safe_urlopen, read_limited, MAX_REMOTE_BYTES
import hashlib, re

def download_to_output(url, item_id, output_root, max_bytes=MAX_REMOTE_BYTES):
    from urllib.parse import urlparse
    if not isinstance(url, str) or not is_civitai_url(url): raise ValueError('下载地址不在允许的 Civitai 域名内')
    if item_id is None: raise ValueError('缺少条目 ID')
    safe_id = str(item_id)
    if not re.fullmatch(r"[0-9]{1,32}", safe_id): raise ValueError('条目 ID 格式无效')
    root=Path(output_root).resolve() / 'ty-node'; root.mkdir(parents=True, exist_ok=True)
    name=f"{safe_id}-{hashlib.sha256(url.encode()).hexdigest()[:12]}.png"; target=root/name; tmp=target.with_suffix('.tmp')
    req=Request(url, headers={'User-Agent':'Mozilla/5.0', 'Referer':'https://civitai.com/'})
    try:
        with safe_urlopen(req, timeout=30) as src:
            final_url = src.geturl() if hasattr(src, 'geturl') else url
            if not is_civitai_url(final_url): raise ValueError('不允许重定向到其他地址')
            payload = read_limited(src, max_bytes)
        tmp.write_bytes(payload)
        tmp.replace(target); return str(Path('ty-node')/name)
    finally:
        if tmp.exists(): tmp.unlink()
