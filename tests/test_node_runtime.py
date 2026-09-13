from PIL import Image
import json
import nodes

def test_node_returns_comfy_ui_result_shape(tmp_path, monkeypatch):
    p=tmp_path/'x.png'; Image.new('RGB',(2,2),(255,0,0)).save(p)
    class FakePage:
        items=[{'id':1,'url':str(p),'meta':{'prompt':'cat'}}]
    class FakeClient:
        def search(self, params): return FakePage()
    monkeypatch.setattr(nodes, 'CivitaiClient', FakeClient)
    out=nodes.CivitaiInspirationLoader().load('civitai.com','', 'Day',1, source='static')
    assert 'ui' in out and 'result' not in out

def test_node_uses_cursor_pages_and_prompt_filter(tmp_path, monkeypatch):
    class FakeCache:
        pages = {}
        def __init__(self, *args, **kwargs): pass
        def get(self, key): return self.pages.get(key)
        def put(self, key, value): self.pages[key] = value
    class FakePage:
        def __init__(self, items, cursor): self.items, self.next_cursor = items, cursor
    calls = []
    class FakeClient:
        def search(self, params):
            calls.append(params.cursor)
            if params.cursor is None:
                return FakePage([{'id': 1, 'url': 'https://image.civitai.com/1.png', 'meta': {}}, {'id': 2, 'url': 'https://image.civitai.com/2.png', 'meta': {'prompt': 'p2'}}], 'cursor-1')
            return FakePage([{'id': 3, 'url': 'https://image.civitai.com/3.png', 'meta': {'prompt': 'p3'}}], None)
    monkeypatch.setattr(nodes, 'Cache', FakeCache)
    monkeypatch.setattr(nodes, 'CivitaiClient', FakeClient)
    monkeypatch.setattr(nodes, '_embedded_prompt', lambda url: {})
    out = nodes.CivitaiInspirationLoader().load('civitai.com', '', 'Day', 2, source='civitai', only_with_prompt=True)
    payload = out['ui']['civitai']
    assert [item['id'] for item in payload] == [2, 3]
    assert calls == [None, 'cursor-1']
    assert json.loads(out['ui']['civitai_info'])['has_next'] is False


def test_node_local_site_reads_downloaded_gallery_without_civitai(monkeypatch):
    local_items = [{
        'id': 'local-example.png', 'url': '/view?filename=ty-node/example.png&type=output',
        'source_url': None, 'has_prompt': True, 'prompt': 'a cat',
        'prompt_status': 'embedded', 'negative_prompt': '', 'metadata': {},
    }]

    class LocalPage:
        items = local_items
        page = 0
        has_next = False
        count = 1

    monkeypatch.setattr(nodes, 'list_local_images', lambda *args, **kwargs: LocalPage())
    monkeypatch.setattr(nodes, '_comfy_output_root', lambda: 'output-root')
    monkeypatch.setattr(nodes, 'CivitaiClient', lambda: (_ for _ in ()).throw(AssertionError('network called')))

    out = nodes.TyHitImageNode().load('local', '', 'Day', 1)

    assert out['ui']['civitai'] == local_items
    info = json.loads(out['ui']['civitai_info'])
    assert info['source'] == 'local'
    assert info['has_next'] is False


def test_node_exposes_local_source_label():
    options = nodes.TyHitImageNode.INPUT_TYPES()['required']['site'][0]
    assert '从本地获取' in options


def test_gallery_item_exposes_models_and_loras():
    item = nodes._gallery_item({"id": 9, "url": "https://image.civitai.com/9.png", "meta": {
        "resources": [{"type": "model", "name": "Base XL"}, {"type": "lora", "name": "Detail"}],
    }}, "civitai.com")
    assert item["models"] == [{"name": "Base XL"}]
    assert item["loras"] == [{"name": "Detail"}]


def test_gallery_item_does_not_treat_hidden_prompt_workflow_as_positive_prompt(monkeypatch):
    class FakeClient:
        def page_metadata(self, site, image_id):
            return {
                'hasPositivePrompt': False,
                'workflow': {'nodes': [{'id': 1}], 'version': 1},
            }

    monkeypatch.setattr(nodes, 'CivitaiClient', FakeClient)
    item = nodes._gallery_item({
        'id': 142564294,
        'url': 'https://image.civitai.com/142564294.png',
        'meta': {'prompt': '{"nodes": [{"id": 1}]}', 'negativePrompt': ''},
    }, 'civitai.com')

    assert item['has_prompt'] is False
    assert item['prompt'] == ''
    assert item['prompt_status'] == 'unavailable'
    assert item['workflow']['version'] == 1
    assert 'prompt' not in item['metadata']
    assert 'negativePrompt' not in item['metadata']


def test_gallery_item_accepts_page_prompt_without_negative_prompt(monkeypatch):
    class FakeClient:
        def page_metadata(self, site, image_id):
            return {'prompt': 'a real prompt'}

    monkeypatch.setattr(nodes, 'CivitaiClient', FakeClient)
    item = nodes._gallery_item({
        'id': 999999991,
        'url': 'https://image.civitai.com/999999991.png',
        'meta': {},
    }, 'civitai.com')

    assert item['prompt'] == 'a real prompt'
    assert item['negative_prompt'] == ''
