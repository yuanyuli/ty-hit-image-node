from pathlib import Path


FRONTEND = Path(__file__).parents[1] / "web" / "civitai_inspiration.js"


def test_local_gallery_contract_is_present():
    """本地历史图片应由前端识别并按只读详情卡片展示。"""
    source = FRONTEND.read_text(encoding="utf-8")
    assert "function isLocalItem" in source
    assert "local === true" in source
    assert "info.source === \"local\"" in source
    assert "本地历史" in source


def test_download_is_skipped_for_local_items():
    source = FRONTEND.read_text(encoding="utf-8")
    # Keep the local branch in the card renderer so a local file is never
    # sent to the Civitai-only download endpoint.
    assert "if (!isLocalItem(item)) actions.append(download);" in source


def test_details_dialog_offers_download_for_remote_items_only():
    source = FRONTEND.read_text(encoding="utf-8")
    assert "const dialogDownload = document.createElement(\"button\");" in source
    assert "if (!local) actions.append(dialogDownload);" in source
