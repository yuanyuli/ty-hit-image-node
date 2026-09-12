from pathlib import Path
from io import BytesIO
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import numpy as np
from PIL import Image

def load_image(path):
    if isinstance(path, str) and path.startswith('https://'):
        req=Request(path, headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Referer':'https://civitai.com/'})
        try: source=BytesIO(urlopen(req, timeout=30).read())
        except HTTPError as exc: raise RuntimeError(f'图片下载失败（HTTP {exc.code}）：Civitai 图片地址拒绝访问') from exc
    else: source=Path(path)
    with Image.open(source) as im:
        arr=np.asarray(im.convert("RGB"),dtype=np.float32)/255.0
    try:
        import torch
        return torch.from_numpy(arr[None,...])
    except ImportError:
        return arr[None,...]

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
