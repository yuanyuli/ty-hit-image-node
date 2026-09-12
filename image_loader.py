from pathlib import Path
from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import numpy as np
from PIL import Image
import warnings
import re
from security import is_civitai_url, safe_urlopen, read_limited, MAX_REMOTE_BYTES

MAX_IMAGE_PIXELS = 50_000_000

def _open_image(source):
    if isinstance(source, Image.Image):
        if source.width * source.height > MAX_IMAGE_PIXELS:
            raise ValueError("图片尺寸超过安全限制")
        return np.asarray(source.convert("RGB"), dtype=np.float32) / 255.0
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(source) as im:
            if im.width * im.height > MAX_IMAGE_PIXELS:
                raise ValueError("图片尺寸超过安全限制")
            return np.asarray(im.convert("RGB"), dtype=np.float32) / 255.0

def load_image(path, max_bytes=MAX_REMOTE_BYTES):
    if isinstance(path, Image.Image):
        arr=_open_image(path)
        try:
            import torch; return torch.from_numpy(arr[None,...])
        except ImportError: return arr[None,...]
    if isinstance(path, str) and path.startswith('https://'):
        if not is_civitai_url(path): raise ValueError('图片地址不在允许的 Civitai 域名内')
        req=Request(path, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer':'https://civitai.com/'})
        try:
            with safe_urlopen(req, timeout=30) as response:
                final_url = response.geturl() if hasattr(response, 'geturl') else path
                if not is_civitai_url(final_url): raise ValueError('不允许重定向到其他地址')
                source=BytesIO(read_limited(response, max_bytes))
        except ValueError: raise
        except HTTPError as exc: raise RuntimeError(f'图片下载失败（HTTP {exc.code}）：Civitai 图片地址拒绝访问') from exc
    else: source=Path(path)
    arr = _open_image(source)
    try:
        import torch
        return torch.from_numpy(arr[None,...])
    except ImportError:
        return arr[None,...]

def read_metadata(path):
    """读取 PNG/JPEG 内嵌参数，供节点补全 prompt。"""
    try:
        if isinstance(path, str) and path.startswith('https://'):
            if not is_civitai_url(path): return {}
            req=Request(path, headers={'User-Agent':'Mozilla/5.0','Referer':'https://civitai.com/'})
            with safe_urlopen(req, timeout=30) as response:
                final_url = response.geturl() if hasattr(response, 'geturl') else path
                if not is_civitai_url(final_url): return {}
                source=BytesIO(read_limited(response))
        else: source=Path(path)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(source) as im:
                if im.width * im.height > MAX_IMAGE_PIXELS: return {}
                info=dict(im.info)
                exif=info.get('exif', b'')
                if isinstance(exif, (bytes, bytearray)):
                    for enc in ('utf-16-be','utf-16-le','utf-8','latin-1'):
                        try:
                            text=bytes(exif).decode(enc, errors='ignore')
                            m=re.search(r'"prompt"\s*:\s*"((?:\\.|[^"\\])*)"', text)
                            if m: info['prompt']=bytes(m.group(1),'utf-8').decode('unicode_escape',errors='ignore'); break
                        except Exception: continue
                return info
    except Exception: return {}

def stack_images(images):
    images=[x.detach().cpu().numpy() if hasattr(x, 'detach') else x for x in images]
    h,w=images[0].shape[1:3]; out=[]
    for x in images:
        im=Image.fromarray(np.clip(x[0]*255,0,255).astype('uint8'))
        scale=min(w/im.width,h/im.height); size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
        im=im.resize(size,Image.Resampling.LANCZOS); canvas=Image.new('RGB',(w,h)); canvas.paste(im,((w-im.width)//2,(h-im.height)//2))
        out.append(np.asarray(canvas,dtype=np.float32)/255.0)
    result=np.stack(out)
    try:
        import torch
        return torch.from_numpy(result)
    except ImportError:
        return result
