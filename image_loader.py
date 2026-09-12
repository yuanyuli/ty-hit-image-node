from pathlib import Path
import numpy as np
from PIL import Image

def load_image(path):
    with Image.open(Path(path)) as im:
        arr=np.asarray(im.convert("RGB"),dtype=np.float32)/255.0
    return arr[None,...]

def stack_images(images):
    h,w=images[0].shape[1:3]; out=[]
    for x in images:
        im=Image.fromarray(np.clip(x[0]*255,0,255).astype('uint8'))
        scale=min(w/im.width,h/im.height); size=(max(1,round(im.width*scale)),max(1,round(im.height*scale)))
        im=im.resize(size,Image.Resampling.LANCZOS); canvas=Image.new('RGB',(w,h)); canvas.paste(im,((w-im.width)//2,(h-im.height)//2))
        out.append(np.asarray(canvas,dtype=np.float32)/255.0)
    return np.stack(out)
