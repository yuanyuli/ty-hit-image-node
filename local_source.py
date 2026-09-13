"""读取节点下载目录中的历史图片。

该模块只允许访问 ComfyUI output 下的 ``ty-node`` 一级目录，并返回可直接
用于 ComfyUI ``/view`` 端点的相对 URL。不会把本机绝对路径放进 UI payload。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from image_loader import read_metadata


IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
MAX_COUNT = 9


@dataclass(frozen=True)
class LocalPage:
    items: list[dict]
    page: int
    count: int
    has_next: bool


def _safe_root(output_root: str | Path) -> Path:
    """返回受保护的历史图根目录，拒绝不存在或非目录的路径。"""

    base = Path(output_root).expanduser().resolve()
    root = (base / "ty-node").resolve()
    # root 必须是 output_root 的直接子目录；resolve 后再次检查可防止
    # output_root 或 ty-node 是指向外部的 junction/symlink。
    if root.parent != base or not root.is_dir():
        return Path()
    return root


def _metadata(path: Path) -> tuple[str, str, dict]:
    try:
        raw = read_metadata(str(path))
    except Exception:
        return "", "", {}
    if not isinstance(raw, dict):
        return "", "", {}
    prompt = next(
        (raw.get(key).strip() for key in ("prompt", "positive_prompt", "positivePrompt")
         if isinstance(raw.get(key), str) and raw.get(key).strip()),
        "",
    )
    negative = next(
        (raw.get(key).strip() for key in ("negativePrompt", "negative_prompt", "negativePromptText")
         if isinstance(raw.get(key), str) and raw.get(key).strip()),
        "",
    )
    try:
        metadata = json.loads(json.dumps(raw, ensure_ascii=False, default=str))
    except (TypeError, ValueError):
        metadata = {}
    return prompt, negative, metadata


def _item(root: Path, path: Path) -> dict:
    name = path.name
    prompt, negative, metadata = _metadata(path)
    # /view performs its own output directory validation. Returning a relative
    # path here keeps the host filesystem path private from the browser.
    view_name = quote(name, safe="")
    view_subfolder = quote("ty-node", safe="")
    return {
        "id": f"local-{name}",
        "url": f"/view?filename={view_name}&subfolder={view_subfolder}&type=output",
        "source_url": None,
        "local": True,
        "source": "local",
        "has_prompt": bool(prompt),
        "prompt": prompt,
        "prompt_status": "embedded" if prompt else "unavailable",
        "negative_prompt": negative,
        "classification": "B" if prompt or metadata else "C",
        "metadata": metadata,
        "author": None,
        "created_at": None,
        "nsfw": False,
        "local_filename": name,
    }


def list_local_images(
    output_root: str | Path,
    count: int = MAX_COUNT,
    page: int = 0,
    query: str = "",
    only_with_prompt: bool = False,
) -> LocalPage:
    """列出历史下载图片，按修改时间倒序分页。

    ``query`` 同时匹配文件名和内嵌正向提示词。仅扫描 ``output_root/ty-node``
    的直接子文件，不跟随链接，也不递归访问其他目录。
    """

    root = _safe_root(output_root)
    if not root:
        return LocalPage([], max(0, int(page or 0)), 0, False)
    size = min(max(int(count or 1), 1), MAX_COUNT)
    page_index = max(int(page or 0), 0)
    needle = str(query or "").strip().casefold()
    candidates = []
    for path in root.iterdir():
        if path.is_symlink() or not path.is_file() or path.suffix.casefold() not in IMAGE_EXTENSIONS:
            continue
        try:
            resolved = path.resolve(strict=True)
            if resolved.parent != root:
                continue
            item = _item(root, path)
            if only_with_prompt and not item["has_prompt"]:
                continue
            if needle and needle not in path.name.casefold() and needle not in item["prompt"].casefold():
                continue
            candidates.append((path.stat().st_mtime_ns, path.name.casefold(), item))
        except (OSError, ValueError):
            continue
    candidates.sort(key=lambda value: (-value[0], value[1]))
    start = page_index * size
    selected = [item for _, _, item in candidates[start:start + size]]
    return LocalPage(selected, page_index, len(candidates), start + size < len(candidates))
