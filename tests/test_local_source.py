from pathlib import Path

from PIL import Image, PngImagePlugin

from local_source import list_local_images


def _image(path: Path, prompt: str | None = None) -> None:
    image = Image.new("RGB", (4, 3), (40, 80, 120))
    if prompt:
        info = PngImagePlugin.PngInfo()
        info.add_text("prompt", prompt)
        image.save(path, pnginfo=info)
    else:
        image.save(path)


def test_lists_only_images_inside_ty_node_with_view_urls(tmp_path):
    output = tmp_path / "output"
    root = output / "ty-node"
    root.mkdir(parents=True)
    _image(root / "new.png", "a cat")
    (root / "notes.txt").write_text("ignore")
    (output / "outside.png").write_bytes(b"must not be listed")

    page = list_local_images(output, count=9)

    assert len(page.items) == 1
    item = page.items[0]
    assert item["id"] == "local-new.png"
    assert item["url"] == "/view?filename=ty-node/new.png&type=output"
    assert item["has_prompt"] is True
    assert item["prompt"] == "a cat"
    assert item["prompt_status"] == "embedded"
    assert item["source_url"] is None


def test_filters_search_and_paginates_newest_first(tmp_path):
    root = tmp_path / "output" / "ty-node"
    root.mkdir(parents=True)
    for name, prompt in (("old.png", "red car"), ("new.png", "blue cat"), ("blue-other.jpg", "")):
        _image(root / name, prompt)
    # Make the ordering deterministic on filesystems with coarse mtime precision.
    import os
    os.utime(root / "old.png", (1, 1))
    os.utime(root / "new.png", (2, 2))
    os.utime(root / "blue-other.jpg", (3, 3))

    page = list_local_images(tmp_path / "output", count=1, page=0, query="blue")

    assert [item["id"] for item in page.items] == ["local-blue-other.jpg"]
    assert page.page == 0
    assert page.has_next is True


def test_only_with_prompt_excludes_workflow_only_metadata(tmp_path):
    root = tmp_path / "output" / "ty-node"
    root.mkdir(parents=True)
    _image(root / "prompt.png", "portrait")
    image = Image.new("RGB", (4, 3), (1, 2, 3))
    info = PngImagePlugin.PngInfo()
    info.add_text("workflow", '{"prompt":"workflow json"}')
    image.save(root / "workflow.png", pnginfo=info)

    page = list_local_images(tmp_path / "output", count=9, only_with_prompt=True)

    assert [item["id"] for item in page.items] == ["local-prompt.png"]


def test_symlinked_image_is_not_allowed_to_escape_directory(tmp_path):
    output = tmp_path / "output"
    root = output / "ty-node"
    root.mkdir(parents=True)
    outside = tmp_path / "outside.png"
    _image(outside, "secret")
    try:
        (root / "escape.png").symlink_to(outside)
    except (OSError, NotImplementedError):
        return

    page = list_local_images(output, count=9)

    assert page.items == []
