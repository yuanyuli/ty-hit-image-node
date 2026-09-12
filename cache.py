import json, os, tempfile
from pathlib import Path
from security import safe_cache_path
class Cache:
    def __init__(self, root): self.root=Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def get(self,key):
        p=safe_cache_path(self.root,key,'.json')
        if not p.exists(): return None
        try: return json.loads(p.read_text(encoding='utf-8'))
        except (OSError, ValueError, TypeError):
            try: p.unlink()
            except OSError: pass
            return None
    def put(self,key,value):
        target=safe_cache_path(self.root,key,'.json')
        fd,tmp=tempfile.mkstemp(prefix='.cache-', dir=self.root)
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f: json.dump(value,f,ensure_ascii=False); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def clear(self,key):
        p=safe_cache_path(self.root,key,'.json')
        if p.exists(): p.unlink()
