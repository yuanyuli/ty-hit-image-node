try:
    from .nodes import TyHitImageNode, CivitaiInspirationLoader
except ImportError:
    import importlib.util, pathlib
    _root = pathlib.Path(__file__).parent
    import sys
    if str(_root) not in sys.path: sys.path.insert(0, str(_root))
    def _load(name):
        spec=importlib.util.spec_from_file_location(f"_civitai_{name}", _root/f"{name}.py")
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod
    TyHitImageNode = _load("nodes").TyHitImageNode
    CivitaiInspirationLoader = _load("nodes").CivitaiInspirationLoader

NODE_CLASS_MAPPINGS = {"TyHitImageNode": TyHitImageNode, "CivitaiInspirationLoader": CivitaiInspirationLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"TyHitImageNode": "ty-hit-image-node", "CivitaiInspirationLoader": "ty-hit-image-node (兼容)"}

WEB_DIRECTORY = "web"

try:
    from aiohttp import web
    import folder_paths
    try: from .download_api import download_to_output
    except ImportError: download_to_output = _load("download_api").download_to_output
    from server import PromptServer
    @PromptServer.instance.routes.post('/civitai-inspiration/download')
    async def _download(request):
        try:
            data=await request.json()
            rel=download_to_output(data.get('url'), data.get('id'), folder_paths.get_output_directory())
            return web.json_response({'filename': rel})
        except Exception as exc:
            return web.json_response({'error': str(exc)}, status=400)
except Exception:
    pass
