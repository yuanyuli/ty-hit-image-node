from dataclasses import dataclass, asdict


def _resource_entry(value):
    if isinstance(value, str) and value.strip():
        return {"name": value.strip()}
    if not isinstance(value, dict):
        return None
    name = value.get("name") or value.get("modelName") or value.get("model")
    digest = value.get("hash") or value.get("modelHash")
    if not isinstance(name, str) or not name.strip():
        if not isinstance(digest, str) or not digest.strip():
            return None
        name = "未命名资源"
    entry = {"name": name.strip()}
    if isinstance(digest, str) and digest.strip():
        entry["hash"] = digest.strip()
    return entry


def _resource_groups(meta):
    models = []
    loras = []
    for key, target in (("models", models), ("loras", loras)):
        values = meta.get(key) or []
        if isinstance(values, (str, dict)):
            values = [values]
        if isinstance(values, list):
            target.extend(entry for entry in (_resource_entry(value) for value in values) if entry)
    resources = meta.get("resources") or []
    if isinstance(resources, dict):
        resources = list(resources.values())
    if isinstance(resources, list):
        for value in resources:
            if not isinstance(value, dict):
                continue
            kind = str(value.get("type") or value.get("resourceType") or "").casefold()
            entry = _resource_entry(value)
            if not entry:
                continue
            if "lora" in kind or "lycoris" in kind:
                loras.append(entry)
            elif kind in {"model", "checkpoint", "ckpt", "vae", "embedding"} or "model" in kind:
                models.append(entry)
    return models, loras

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
    models, loras = _resource_groups(meta)
    return NormalizedMetadata(cls, prompt, neg, models, loras, meta, summary)
