from PIL import Image
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
    assert out['ui']['civitai_info']['has_next'] is False
