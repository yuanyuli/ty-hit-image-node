from dataclasses import dataclass
from urllib.parse import urlencode
import json, urllib.request, urllib.error, os, time, html


def _iter_json_key_values(text, key):
    """只匹配 JSON 字符串外层的 key，忽略嵌套序列化字符串。"""
    decoder = json.JSONDecoder()
    index = 0
    while index < len(text):
        if text[index] != '"':
            index += 1
            continue
        start = index
        index += 1
        escaped = False
        while index < len(text):
            char = text[index]
            index += 1
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                break
        try:
            name = json.loads(text[start:index])
        except (ValueError, TypeError):
            continue
        cursor = index
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if name != key or cursor >= len(text) or text[cursor] != ':':
            continue
        cursor += 1
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        try:
            value, _ = decoder.raw_decode(text, cursor)
        except (ValueError, TypeError):
            continue
        yield value


def _extract_json_value(text, key):
    """从包含任意脚本内容的文本中读取 key 对应的一个 JSON 值。"""
    return next(_iter_json_key_values(text, key), None)


def _extract_meta_prompt(text):
    """寻找含 prompt 字段的页面 meta 对象，避免依赖字段顺序。"""
    for value in _iter_json_key_values(text, 'meta'):
        if isinstance(value, dict) and isinstance(value.get('prompt'), str):
            return value
    return {}

@dataclass(frozen=True)
class QueryParams:
    site: str = "civitai.com"
    prompt_query: str = ""
    period: str = "Day"
    media_type: str = "image"
    count: int = 10
    sfw: bool = True
    cursor: str | None = None
    # Civitai image API currently accepts the following public sort values.
    # Keep this as a query option instead of sorting locally: cursor pagination
    # only remains stable when the server owns the ordering.
    sort: str = "Most Reactions"
    tag_id: int | None = None

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
        allowed_sorts = {
            "Most Reactions", "Most Comments", "Most Collected",
            "Newest", "Oldest",
        }
        sort = params.sort if params.sort in allowed_sorts else "Most Reactions"
        q={"limit": min(max(params.count,1),20), "period":params.period, "sort":sort, "nsfw":str(not params.sfw).lower()}
        if params.media_type in ("image", "video"): q["type"] = params.media_type
        if params.prompt_query: q["query"]=params.prompt_query[:256]
        if params.tag_id: q["tags"] = params.tag_id
        if params.cursor: q["cursor"] = params.cursor
        data=self._request_json(base+"?"+urlencode(q)); items=data.get("items", [])[:q["limit"]]
        meta=data.get("metadata") or {}; return SearchPage(items, meta.get("nextCursor"))

    def page_metadata(self, site, image_id):
        """从公开图片页的嵌入状态读取 prompt、可见性标记和 workflow。"""
        if site not in self.BASE or not str(image_id).isdigit(): return {}
        req=urllib.request.Request(f"https://{site}/images/{image_id}", headers={"User-Agent":"Mozilla/5.0","Referer":"https://civitai.com/"})
        try:
            try:
                with urllib.request.urlopen(req, timeout=15) as r: text=html.unescape(r.read(2_000_000).decode('utf-8','ignore'))
            except Exception:
                if site != 'civitai.com':
                    fallback=urllib.request.Request(f"https://civitai.com/images/{image_id}", headers={"User-Agent":"Mozilla/5.0","Referer":"https://civitai.com/"})
                    with urllib.request.urlopen(fallback, timeout=15) as r: text=html.unescape(r.read(2_000_000).decode('utf-8','ignore'))
                else: return {}
            result = {}
            flag = _extract_json_value(text, 'hasPositivePrompt')
            if isinstance(flag, bool):
                result['hasPositivePrompt'] = flag

            meta = _extract_meta_prompt(text)
            if flag is not False and isinstance(meta.get('prompt'), str):
                result['prompt'] = meta['prompt']
                negative = meta.get('negativePrompt') or meta.get('negative_prompt')
                if isinstance(negative, str):
                    result['negativePrompt'] = negative

            workflow = _extract_json_value(text, 'workflow')
            if isinstance(workflow, str):
                try:
                    parsed = json.loads(workflow)
                except (TypeError, ValueError):
                    parsed = None
                workflow = parsed if isinstance(parsed, (dict, list)) else None
            if isinstance(workflow, (dict, list)):
                result['workflow'] = workflow
            return result
        except Exception: return {}
