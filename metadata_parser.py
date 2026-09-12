from dataclasses import dataclass, asdict

@dataclass
class NormalizedMetadata:
    classification: str
    prompt: str = ""
    negative_prompt: str = ""
    models: list = None
    loras: list = None
    parameters: dict = None
    workflow_summary: dict | None = None

def normalize_item(item):
    meta=item.get("meta") or item.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    prompt=meta.get("prompt") or item.get("prompt") or ""
    neg=meta.get("negativePrompt") or meta.get("negative_prompt") or ""
    workflow=meta.get("workflow") or item.get("workflow")
    cls="A" if workflow else ("B" if prompt or meta else "C")
    summary={"present": True} if workflow else None
    return NormalizedMetadata(cls, prompt, neg, meta.get("models") or [], meta.get("loras") or [], meta, summary)
