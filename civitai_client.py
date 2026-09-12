from dataclasses import dataclass
from urllib.parse import urlencode
import json, urllib.request, urllib.error, os, time

@dataclass(frozen=True)
class QueryParams:
    site: str = "civitai.com"
    prompt_query: str = ""
    period: str = "Day"
    media_type: str = "image"
    count: int = 10
    sfw: bool = True

class ApiError(RuntimeError):
    def __init__(self, status, message): self.status, self.message = status, message; super().__init__(message)

@dataclass
class SearchPage:
    items: list
    next_cursor: str | None = None

class CivitaiClient:
    BASE = {"civitai.com":"https://civitai.com/api/v1/images", "civitai.red":"https://civitai.red/api/v1/images"}
    def _request_json(self, url):
        last = None
        for attempt in range(3):
            try:
                req=urllib.request.Request(url, headers={"User-Agent":"ty-civitai-gallery/0.1"})
                key=os.getenv('CIVITAI_API_KEY')
                if key: req.add_header('Authorization', f'Bearer {key}')
                with urllib.request.urlopen(req, timeout=15) as r: return json.load(r)
            except urllib.error.HTTPError as e:
                last=e
                if e.code not in (429, 500, 502, 503, 504) or attempt == 2: break
                time.sleep(0.8 * (2 ** attempt))
            except Exception as e:
                last=e; break
        if isinstance(last, urllib.error.HTTPError):
            msgs={403:"需要授权或内容不可见",404:"资源不存在",429:"请求过于频繁",503:"Civitai 暂时不可用，请稍后重试"}
            raise ApiError(last.code, msgs.get(last.code, f"HTTP {last.code}")) from last
        raise ApiError(0, f"网络请求失败: {last}") from last
    def search(self, params):
        base=self.BASE.get(params.site)
        if not base: raise ValueError(f"不支持的站点: {params.site}")
        q={"limit": min(max(params.count,1),20), "period":params.period, "sort":"Most Reactions", "nsfw":str(params.sfw).lower()}
        if params.media_type in ("image", "video"): q["type"] = params.media_type
        if params.prompt_query: q["query"]=params.prompt_query[:256]
        data=self._request_json(base+"?"+urlencode(q)); items=data.get("items", [])[:q["limit"]]
        meta=data.get("metadata") or {}; return SearchPage(items, meta.get("nextCursor"))
