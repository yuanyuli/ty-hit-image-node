from pathlib import Path
from image_loader import load_image

class CivitaiImageLoader:
    @classmethod
    def INPUT_TYPES(cls): return {'required': {'filename': ('STRING', {'default':'','multiline':False})}}
    RETURN_TYPES=('IMAGE',); RETURN_NAMES=('image',); FUNCTION='load'; CATEGORY='Civitai/Inspiration'
    def load(self, filename):
        root=Path(__file__).resolve().parent/'output'/'ty-node'
        path=(root/filename).resolve()
        if root not in path.parents: raise RuntimeError('只能读取 output/ty-node 目录中的文件')
        if not path.is_file(): raise RuntimeError(f'文件不存在: {filename}')
        return (load_image(path),)
