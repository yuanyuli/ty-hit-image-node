from pathlib import Path
from urllib.request import urlopen
from security import allowed_url
import hashlib, shutil

def download_to_output(url, item_id, output_root):
    from urllib.parse import urlparse
    host=urlparse(url).hostname
    if not host or not allowed_url(url, host): raise ValueError('下载地址不在允许的 Civitai 域名内')
    if item_id is None: raise ValueError('缺少条目 ID')
    root=Path(output_root).resolve() / 'ty-node'; root.mkdir(parents=True, exist_ok=True)
    name=f"{item_id}-{hashlib.sha256(url.encode()).hexdigest()[:12]}.png"; target=root/name; tmp=target.with_suffix('.tmp')
    with urlopen(url, timeout=30) as src, tmp.open('wb') as dst:
        shutil.copyfileobj(src,dst,1024*64)
        if tmp.stat().st_size > 50*1024*1024: tmp.unlink(); raise ValueError('图片超过 50MB 限制')
    tmp.replace(target); return str(Path('ty-node')/name)
