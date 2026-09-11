import json
from pathlib import Path
from security import safe_cache_path
class Cache:
    def __init__(self, root): self.root=Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def get(self,key):
        p=safe_cache_path(self.root,key,'.json')
        if not p.exists(): return None
        return json.loads(p.read_text(encoding='utf-8'))
    def put(self,key,value): safe_cache_path(self.root,key,'.json').write_text(json.dumps(value),encoding='utf-8')
    def clear(self,key):
        p=safe_cache_path(self.root,key,'.json')
        if p.exists(): p.unlink()
