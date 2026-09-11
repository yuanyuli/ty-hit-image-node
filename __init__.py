try:
    from .nodes import CivitaiInspirationLoader
except ImportError:
    from nodes import CivitaiInspirationLoader

NODE_CLASS_MAPPINGS = {"CivitaiInspirationLoader": CivitaiInspirationLoader}
NODE_DISPLAY_NAME_MAPPINGS = {"CivitaiInspirationLoader": "Civitai 灵感图加载器"}
