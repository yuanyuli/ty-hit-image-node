from dataclasses import dataclass
from urllib.parse import urlencode
import json, urllib.request

@dataclass(frozen=True)
class QueryParams:
    site: str = "civitai.com"
    prompt_query: str = ""
    period: str = "Day"
    media_type: str = "image"
    count: int = 10

class ApiError(RuntimeError):
    def __init__(self, status, message): self.status, self.message = status, message; super().__init__(message)

@dataclass
class SearchPage:
    items: list
    next_cursor: str | None = None

class CivitaiClient:
    BASE = {"civitai.com":"https://civitai.com/api/v1/images", "civitai.red":"https://civitai.red/api/v1/images"}
    def _request_json(self, url):
        try:
            with urllib.request.urlopen(url, timeout=15) as r: return json.load(r)
        except urllib.error.HTTPError as e:
            msgs={403:"需要授权或内容不可见",404:"资源不存在",429:"请求过于频繁"}
            raise ApiError(e.code, msgs.get(e.code, f"HTTP {e.code}")) from e
        except Exception as e: raise ApiError(0, f"网络请求失败: {e}") from e
    def search(self, params):
        base=self.BASE.get(params.site)
        if not base: raise ValueError(f"不支持的站点: {params.site}")
        q={"limit": min(max(params.count,1),20), "period":params.period, "sort":"Most Reactions", "nsfw":"None" if True else ""}
        if params.prompt_query: q["query"]=params.prompt_query[:256]
        data=self._request_json(base+"?"+urlencode(q)); items=data.get("items", [])[:q["limit"]]
        meta=data.get("metadata") or {}; return SearchPage(items, meta.get("nextCursor"))
