import json
from civitai_client import CivitaiClient, QueryParams, ApiError
from metadata_parser import normalize_item
from image_loader import load_image, stack_images

class CivitaiInspirationLoader:
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
    FUNCTION = "load"
    CATEGORY = "Civitai/Inspiration"

    def load(self, site, prompt_query, period, media_type, count, result_index, model='', family='', base_model='', lora='', sfw=True, refresh=False):
        try:
            page=CivitaiClient().search(QueryParams(site, prompt_query, period, media_type, count))
        except ApiError as exc:
            if exc.status == 403:
                raise RuntimeError(f'Civitai 拒绝访问（403）：{exc.message}。如该站点要求授权，请设置环境变量 CIVITAI_API_KEY 后重启 ComfyUI。') from exc
            raise RuntimeError(f'Civitai 请求失败（{exc.status}）：{exc.message}') from exc
        if result_index > len(page.items): raise RuntimeError(f'结果序号 {result_index} 越界，当前只有 {len(page.items)} 条结果')
        selected=page.items[result_index-1]; normalized=normalize_item(selected)
        url=selected.get('url') or selected.get('imageUrl') or selected.get('thumbnailUrl')
        if not url: raise RuntimeError('选中的条目没有可用图片或预览图地址')
        image=load_image(url) if isinstance(url, str) and url.startswith('http') else load_image(url)
        batch=stack_images([image])
        meta=json.dumps({'id':selected.get('id'),'classification':normalized.classification,'prompt':normalized.prompt,'negative_prompt':normalized.negative_prompt}, ensure_ascii=False)
        return {"ui": {"civitai": [{"id": selected.get("id"), "url": url}]}, "result": (image, normalized.prompt, normalized.negative_prompt, meta, url, batch)}
