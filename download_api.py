from pathlib import Path
from urllib.request import urlopen
from security import allowed_url
import hashlib, shutil

def download_to_output(url, item_id, output_root):
    if not allowed_url(url, url.split('/')[2]): raise ValueError('下载地址不在允许的 Civitai 域名内')
    root=Path(output_root).resolve() / 'ty-node'; root.mkdir(parents=True, exist_ok=True)
    name=f"{item_id}-{hashlib.sha256(url.encode()).hexdigest()[:12]}.png"; target=root/name; tmp=target.with_suffix('.tmp')
    with urlopen(url, timeout=30) as src, tmp.open('wb') as dst: shutil.copyfileobj(src,dst,1024*64)
    tmp.replace(target); return str(Path('ty-node')/name)
