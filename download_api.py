from pathlib import Path
from urllib.request import Request, urlopen
from security import is_civitai_url, safe_urlopen, read_limited, MAX_REMOTE_BYTES
import hashlib, re
from urllib.parse import urlparse

def _extension(response, url):
    """根据响应类型选择安全的图片扩展名，无法判断时回退 png。"""
    content_type = ''
    try:
        content_type = (response.headers.get('Content-Type') or '').split(';', 1)[0].lower()
    except Exception:
        pass
    by_type = {'image/jpeg': '.jpg', 'image/jpg': '.jpg', 'image/webp': '.webp', 'image/gif': '.gif', 'image/png': '.png'}
    if content_type in by_type:
        return by_type[content_type]
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {'.jpg', '.jpeg', '.png', '.webp', '.gif'} else '.png'

def download_to_output(url, item_id, output_root, max_bytes=MAX_REMOTE_BYTES):
    if not isinstance(url, str) or not is_civitai_url(url): raise ValueError('下载地址不在允许的 Civitai 域名内')
    if item_id is None: raise ValueError('缺少条目 ID')
    safe_id = str(item_id)
    if not re.fullmatch(r"[0-9]{1,32}", safe_id): raise ValueError('条目 ID 格式无效')
    root=Path(output_root).resolve() / 'ty-node'; root.mkdir(parents=True, exist_ok=True)
    req=Request(url, headers={'User-Agent':'Mozilla/5.0', 'Referer':'https://civitai.com/'})
    target = None
    tmp = None
    try:
        with safe_urlopen(req, timeout=30) as src:
            final_url = src.geturl() if hasattr(src, 'geturl') else url
            if not is_civitai_url(final_url): raise ValueError('不允许重定向到其他地址')
            content_type = ''
            try:
                content_type = (src.headers.get('Content-Type') or '').split(';', 1)[0].lower()
            except Exception:
                pass
            if content_type and not content_type.startswith('image/'):
                raise ValueError('下载地址返回的内容不是图片')
            payload = read_limited(src, max_bytes)
            name=f"{safe_id}-{hashlib.sha256(url.encode()).hexdigest()[:12]}{_extension(src, final_url)}"
            target=root/name; tmp=target.with_suffix('.tmp')
        tmp.write_bytes(payload)
        tmp.replace(target); return str(Path('ty-node')/name)
    finally:
        if tmp is not None and tmp.exists(): tmp.unlink()
