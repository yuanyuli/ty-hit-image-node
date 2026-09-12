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
