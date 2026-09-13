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


def test_site_widget_supports_right_click_cycle():
    source = FRONTEND.read_text(encoding="utf-8")
    assert "function cycleEnumWidget" in source
    assert "event?.button === 2" in source
    assert "function enumWidgetAt" in source
    assert "installCanvasEnumCycling" in source
    assert "addEventListener(\"contextmenu\"" in source
    assert "preventDefault();" in source


def test_details_dialog_includes_model_and_lora_sections():
    source = FRONTEND.read_text(encoding="utf-8")
    assert "function resourceLabel" in source
    assert "模型" in source
    assert "LoRA" in source


def test_details_dialog_offers_workflow_copy_separately_from_prompt():
    source = FRONTEND.read_text(encoding="utf-8")
    assert "复制工作流" in source
    assert "JSON.stringify(item.workflow, null, 2)" in source
    assert "has_workflow" in source
