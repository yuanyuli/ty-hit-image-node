try:
    from .nodes import CivitaiInspirationLoader
    from .image_node import CivitaiImageLoader
except ImportError:
    from nodes import CivitaiInspirationLoader
    from image_node import CivitaiImageLoader

NODE_CLASS_MAPPINGS = {"CivitaiInspirationLoader": CivitaiInspirationLoader, "CivitaiImageLoader": CivitaiImageLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"CivitaiInspirationLoader": "Civitai 灵感图加载器", "CivitaiImageLoader": "Civitai 图片加载器"}

WEB_DIRECTORY = "web"

try:
    from aiohttp import web
    import folder_paths
    from .download_api import download_to_output
    from server import PromptServer
    @PromptServer.instance.routes.post('/civitai-inspiration/download')
    async def _download(request):
        data=await request.json()
        rel=download_to_output(data.get('url'), data.get('id'), folder_paths.get_output_directory())
        return web.json_response({'filename': rel})
except Exception:
    pass
