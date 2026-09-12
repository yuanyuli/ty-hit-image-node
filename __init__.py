try:
    from .nodes import CivitaiInspirationLoader
    from .image_node import CivitaiImageLoader
except ImportError:
    from nodes import CivitaiInspirationLoader
    from image_node import CivitaiImageLoader

NODE_CLASS_MAPPINGS = {"CivitaiInspirationLoader": CivitaiInspirationLoader, "CivitaiImageLoader": CivitaiImageLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"CivitaiInspirationLoader": "Civitai 灵感图加载器", "CivitaiImageLoader": "Civitai 图片加载器"}
