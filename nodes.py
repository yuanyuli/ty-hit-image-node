import json
import hashlib
from pathlib import Path
from civitai_client import CivitaiClient, QueryParams, ApiError
from metadata_parser import normalize_item
from image_loader import load_image, stack_images, read_metadata
from cache import Cache

class CivitaiInspirationLoader:
    OUTPUT_NODE = True
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "site": (['civitai.com','civitai.red'],), "prompt_query": ('STRING', {'default':'','multiline':False}),
            "period": (['Day','Week','Month','AllTime'],), "media_type": (['image','video'],),
            "count": ('INT', {'default':10,'min':1,'max':20}), "result_index": ('INT', {'default':1,'min':1,'max':20}),
            "model": ('STRING', {'default':''}), "family": ('STRING', {'default':''}), "base_model": ('STRING', {'default':''}),
            "lora": ('STRING', {'default':''}), "sfw": ('BOOLEAN', {'default':True}), "refresh": ('BOOLEAN', {'default':False})}}

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("image", "prompt", "negative_prompt", "metadata", "source_url", "batch")
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return tuple(kwargs.get(k) for k in ('site','prompt_query','period','media_type','count','result_index','model','family','base_model','lora','sfw','refresh'))
    FUNCTION = "load"
    CATEGORY = "Civitai/Inspiration"

    def load(self, site, prompt_query, period, media_type, count, result_index, model='', family='', base_model='', lora='', sfw=True, refresh=False):
        cache=Cache(Path(__file__).resolve().parent/'.cache')
        cache_key=hashlib.sha256(json.dumps(['v3',site,prompt_query,period,media_type,count,model,family,base_model,lora,sfw], ensure_ascii=False).encode()).hexdigest()
        try:
            cached=cache.get(cache_key)
            if cached is not None:
                invalid=any(isinstance(x, dict) and isinstance(x.get('url'), str) and not x['url'].startswith('http') and not Path(x['url']).exists() for x in cached)
                if invalid: cache.clear(cache_key); cached=None
            if cached is not None and not refresh: page_items=cached
            else:
                try:
                    page_items=CivitaiClient().search(QueryParams(site, prompt_query, period, media_type, count, sfw)).items
                    cache.put(cache_key, page_items)
                except ApiError:
                    if cached is None: raise
                    page_items=cached
        except ApiError as exc:
            if exc.status == 403:
                raise RuntimeError(f'Civitai 拒绝访问（403）：{exc.message}。如该站点要求授权，请设置环境变量 CIVITAI_API_KEY 后重启 ComfyUI。') from exc
            raise RuntimeError(f'Civitai 请求失败（{exc.status}）：{exc.message}') from exc
        if result_index > len(page_items): raise RuntimeError(f'结果序号 {result_index} 越界，当前只有 {len(page_items)} 条结果')
        selected=page_items[result_index-1]
        if not (selected.get('meta') or selected.get('metadata')) and selected.get('id'):
            try:
                detail=CivitaiClient()._request_json(CivitaiClient.BASE[site] + '?imageId=' + str(selected['id']))
                if detail.get('items'): selected=detail['items'][0]
            except Exception: pass
        normalized=normalize_item(selected)
        url=selected.get('url') or selected.get('imageUrl') or selected.get('thumbnailUrl')
        if not url: raise RuntimeError('选中的条目没有可用图片或预览图地址')
        image=load_image(url) if isinstance(url, str) and url.startswith('http') else load_image(url)
        if not normalized.prompt:
            embedded=read_metadata(url)
            raw=embedded.get('parameters') or embedded.get('prompt') or ''
            if raw:
                normalized.prompt = str(raw)
        batch_images=[image]
        seen={selected.get('id')}
        for item in page_items:
            if item.get('id') in seen: continue
            other=item.get('url') or item.get('imageUrl') or item.get('thumbnailUrl')
            if not other: continue
            try: batch_images.append(load_image(other)); seen.add(item.get('id'))
            except Exception: continue
            if len(batch_images) >= min(count,9): break
        batch=stack_images(batch_images)
        meta=json.dumps({'id':selected.get('id'),'classification':normalized.classification,'prompt':normalized.prompt,'negative_prompt':normalized.negative_prompt}, ensure_ascii=False)
        gallery=[{"id": x.get("id"), "url": x.get("url") or x.get("imageUrl") or x.get("thumbnailUrl")} for x in page_items]
        return {"ui": {"civitai": gallery}, "result": (image, normalized.prompt, normalized.negative_prompt, meta, url, batch)}
