class CivitaiInspirationLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("image", "prompt", "negative_prompt", "metadata", "source_url", "batch")
    FUNCTION = "load"
    CATEGORY = "Civitai/Inspiration"

    def load(self, **kwargs):
        raise RuntimeError("节点尚未完成实现")
