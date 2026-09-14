import json
import hashlib
import io, base64
from pathlib import Path
from urllib.parse import quote
from civitai_client import CivitaiClient, QueryParams, ApiError
from metadata_parser import normalize_item
from image_loader import read_metadata
from cache import Cache
from local_source import list_local_images

SORT_OPTIONS = ['Most Reactions', 'Most Comments', 'Most Collected', 'Newest', 'Oldest']
IMAGE_TAG_IDS = {'全部': None, 'Anime': 4, 'Beach': 5998, 'Fantasy': 5207,
                 'Portrait': 1441, 'Landscape': 8363}
MAX_COUNT = 9
NODE_VERSION = 'v7'
_META_CACHE = {}


def _comfy_output_root():
    """返回 ComfyUI output 根目录；脱离 ComfyUI 测试时使用本地回退目录。"""
    try:
        import folder_paths
        return folder_paths.get_output_directory()
    except Exception:
        return Path(__file__).resolve().parent / 'output'

def _embedded_prompt(url):
    if not isinstance(url, str) or not url.startswith('https://'):
        return {}
    try:
        info = read_metadata(url)
    except Exception:
        return {}
    if not isinstance(info, dict):
        return {}
    prompt = next((info.get(k) for k in ('prompt', 'positive_prompt', 'positivePrompt') if isinstance(info.get(k), str) and info.get(k).strip()), '')
    if not prompt:
        return {}
    return {'prompt': prompt.strip(), 'negativePrompt': info.get('negativePrompt') or info.get('negative_prompt') or ''}


def _looks_like_workflow(value):
    if not isinstance(value, str):
        return isinstance(value, (dict, list)) and (isinstance(value, list) or any(k in value for k in ('nodes', 'prompt', 'workflow')))
    text = value.strip()
    if not text or text[0] not in '[{':
        return False
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        return False
    return _looks_like_workflow(parsed)

def _gallery_item(item, site):
    url = item.get('url') or item.get('imageUrl') or item.get('thumbnailUrl')
    meta = item.get('meta') or item.get('metadata') or {}
    normalized = normalize_item(item)
    # API responses from third-party mirrors can contain non-string prompt
    # values. Treat those as missing metadata instead of breaking the gallery.
    if not isinstance(normalized.prompt, str):
        normalized.prompt = ''
    if not isinstance(normalized.negative_prompt, str):
        normalized.negative_prompt = ''
    prompt_status = 'api' if normalized.prompt else 'unknown'
    meta_key=(site, item.get('id'))
    api_prompt_is_workflow = _looks_like_workflow(normalized.prompt)
    embedded = _META_CACHE.get(meta_key) if item.get('id') and (not normalized.prompt or api_prompt_is_workflow or item.get('hasPositivePrompt') is False) else {}
    if embedded is None:
        try: embedded = CivitaiClient().page_metadata(site, item.get('id'))
        except Exception: embedded = {}
        _META_CACHE[meta_key] = embedded
    if not embedded and not normalized.prompt:
        embedded = _embedded_prompt(url) if not normalized.prompt else {}
    page_hides_prompt = isinstance(embedded, dict) and embedded.get('hasPositivePrompt') is False
    if page_hides_prompt or (embedded.get('workflow') and not embedded.get('prompt') and api_prompt_is_workflow):
        normalized.prompt = ''
        normalized.negative_prompt = ''
        meta = {key: value for key, value in meta.items() if key not in ('prompt', 'negativePrompt', 'negative_prompt')}
        prompt_status = 'unavailable'
    elif embedded.get('prompt'):
        normalized.prompt = embedded['prompt']
        normalized.negative_prompt = embedded.get('negativePrompt') or embedded.get('negative_prompt') or ''
        if not isinstance(normalized.negative_prompt, str):
            normalized.negative_prompt = ''
        meta = {**meta, **embedded}
        prompt_status = 'page'
    elif not normalized.prompt:
        prompt_status = 'unavailable'
    if embedded.get('workflow'):
        meta = {**meta, 'workflow': embedded['workflow']}
    item_id = item.get('id')
    source_url = item.get('source_url') or (f"https://{site}/images/{quote(str(item_id), safe='')}" if item_id is not None else None)
    try:
        metadata = json.loads(json.dumps(meta, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        metadata = {}
    user = item.get('user')
    author = user.get('username') if isinstance(user, dict) else item.get('username')
    return {'id': item_id, 'url': url, 'source_url': source_url,
            'has_prompt': bool(normalized.prompt.strip()), 'prompt': normalized.prompt,
            'prompt_status': prompt_status,
            'negative_prompt': normalized.negative_prompt, 'classification': normalized.classification,
            'models': normalized.models or [], 'loras': normalized.loras or [],
            'workflow': meta.get('workflow'), 'has_workflow': bool(meta.get('workflow')),
            'metadata': metadata, 'author': author,
            'created_at': item.get('createdAt') or item.get('created_at'),
            'nsfw': bool(item.get('nsfw', False))}

class TyHitImageNode:
    OUTPUT_NODE = True
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "site": (['civitai.com','civitai.red','从本地获取'], {'default':'civitai.com'}), "prompt_query": ('STRING', {'default':'','multiline':False}),
            "period": (['Day','Week','Month','AllTime'], {'default':'Day'}),
            "count": ('INT', {'default':9,'min':1,'max':MAX_COUNT}),
            "sfw": ('BOOLEAN', {'default':True})}, "optional": {
                "sort": (SORT_OPTIONS, {'default':'Most Reactions'}),
                "image_tag": (list(IMAGE_TAG_IDS), {'default':'全部'}),
                # Internal compatibility field. Keep it open-ended so workflows
                # that serialized a legacy combo index (for example 4) can load.
                "source": ('STRING', {'default':'civitai', 'hidden': True}),
                "page": ('INT', {'default':0,'min':0,'max':1000, 'hidden': True}),
                "refresh": ('BOOLEAN', {'default':False, 'hidden': True}),
                "only_with_prompt": ('BOOLEAN', {'default':False})}}

    RETURN_TYPES = ()
    RETURN_NAMES = ()
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return tuple(kwargs.get(k) for k in ('site','prompt_query','period','count','sfw','sort','image_tag','refresh','source','page','only_with_prompt'))
    FUNCTION = "load"
    CATEGORY = "Civitai/Inspiration"

    def load(self, site, prompt_query, period, count, sfw=True, sort='Most Reactions', refresh=False, source='civitai', page=0, only_with_prompt=False, image_tag='全部'):
        count = min(max(int(count), 1), MAX_COUNT)
        sort = sort if sort in SORT_OPTIONS else 'Most Reactions'
        source = source if source in ('static', 'civitai') else 'civitai'
        image_tag = image_tag if image_tag in IMAGE_TAG_IDS else '全部'
        cache = Cache(Path(__file__).resolve().parent/'.cache')
        page_index = int(page or 0)
        stale_state = {'used': False}

        if site in ('local', '从本地获取'):
            local_page = list_local_images(
                _comfy_output_root(), count=count, page=page_index,
                query=prompt_query or '', only_with_prompt=bool(only_with_prompt),
            )
            info = {
                'page': local_page.page, 'count': len(local_page.items),
                'requested_count': count, 'next_cursor': None,
                'has_next': local_page.has_next, 'sort': sort,
                'source': 'local', 'stale': False,
            }
            return {'ui': {
                'civitai': local_page.items,
                'civitai_info': json.dumps(info, ensure_ascii=False),
            }}

        def page_key(index):
            payload = ['v7', site, (prompt_query or '')[:256], period, count, bool(sfw), sort, source, image_tag, index]
            return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode()).hexdigest()

        def get_page(index, force=False):
            cursor = None
            items, next_cursor = [], None
            for current in range(index + 1):
                cached = None if force and current == index else cache.get(page_key(current))
                if isinstance(cached, dict) and isinstance(cached.get('items'), list):
                    items, next_cursor = cached['items'], cached.get('next_cursor')
                elif isinstance(cached, list):
                    items, next_cursor = cached, None
                else:
                    if current and not cursor:
                        return [], None
                    try:
                        result = CivitaiClient().search(QueryParams(site, prompt_query or '', period, 'image', count, sfw, cursor, sort, IMAGE_TAG_IDS[image_tag]))
                    except ApiError:
                        # refresh is best effort: retain a previously cached page
                        # when Civitai is temporarily unavailable.
                        stale = cache.get(page_key(current))
                        if isinstance(stale, dict) and isinstance(stale.get('items'), list):
                            items, next_cursor = stale['items'], stale.get('next_cursor')
                            stale_state['used'] = True
                            continue
                        if isinstance(stale, list):
                            items, next_cursor = stale, None
                            stale_state['used'] = True
                            continue
                        raise
                    items, next_cursor = list(result.items), result.next_cursor
                    cache.put(page_key(current), {'items': items, 'next_cursor': next_cursor})
                cursor = next_cursor
            return items, next_cursor

        try:
            if source == 'static':
                from PIL import Image, ImageDraw
                page_items=[]
                start = 1 + page_index * count
                for i in range(start, start + count):
                    im=Image.new('RGB',(256,256),((i*37)%255,(i*71)%255,(i*109)%255)); ImageDraw.Draw(im).text((20,110),f'STATIC {i}',fill='white')
                    buf=io.BytesIO(); im.save(buf,'PNG'); data='data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()
                    page_items.append({'id':f'static-{i}','url':data,'meta':{'prompt':f'static test prompt {i}','negativePrompt':'static test negative'}})
                next_cursor = None
            else:
                page_items, next_cursor = get_page(page_index, bool(refresh))
                if only_with_prompt:
                    # Continue through server pages until count prompt-bearing entries are found.
                    selected=[]; seen=set(); current_page=page_index
                    while True:
                        for item in page_items:
                            entry = _gallery_item(item, site); key = entry.get('id') or entry.get('url')
                            if entry['has_prompt'] and key not in seen:
                                selected.append(item); seen.add(key)
                        if len(selected) >= count or not next_cursor or current_page >= 1000:
                            page_items, page_index = selected[:count], current_page
                            break
                        current_page += 1
                        page_items, next_cursor = get_page(current_page)
        except ApiError as exc:
            if exc.status == 403:
                raise RuntimeError(f'Civitai 拒绝访问（403）：{exc.message}。如该站点要求授权，请设置环境变量 CIVITAI_API_KEY 后重启 ComfyUI。') from exc
            raise RuntimeError(f'Civitai 请求失败（{exc.status}）：{exc.message}') from exc

        gallery=[]; seen=set()
        for x in page_items:
            entry = _gallery_item(x, site)
            if only_with_prompt and not entry['has_prompt']: continue
            key = entry.get('id') or entry.get('url')
            if key in seen: continue
            seen.add(key); gallery.append(entry)
            if len(gallery) >= count: break
        info = {'page': page_index, 'count': len(gallery), 'requested_count': count, 'next_cursor': next_cursor, 'has_next': bool(next_cursor), 'sort': sort, 'source': source, 'stale': stale_state['used']}
        return {'ui': {'civitai': gallery, 'civitai_info': json.dumps(info, ensure_ascii=False)}}

# 兼容早期已保存的 workflow。
CivitaiInspirationLoader = TyHitImageNode
