from PIL import Image
from image_loader import load_image, stack_images

def test_load_image_returns_normalized_tensor_shape(tmp_path):
    p=tmp_path/'a.png'; Image.new('RGB',(4,2),(255,0,0)).save(p)
    x=load_image(p)
    assert tuple(x.shape)==(1,2,4,3)
    assert float(x.max()) <= 1.0

def test_stack_images_pads_to_first_size(tmp_path):
    a=tmp_path/'a.png'; b=tmp_path/'b.png'; Image.new('RGB',(4,2)).save(a); Image.new('RGB',(2,1)).save(b)
    x=stack_images([load_image(a),load_image(b)])
    assert tuple(x.shape)==(2,2,4,3)
import pytest

def test_remote_image_rejects_untrusted_host():
    from image_loader import load_image
    with pytest.raises(ValueError, match="允许的 Civitai"):
        load_image("https://evil.example/image.png")

def test_remote_image_enforces_size_limit(monkeypatch):
    import image_loader
    class Response:
        headers = {"Content-Length": "10"}
        def __enter__(self): return self
        def __exit__(self, *args): pass
    monkeypatch.setattr(image_loader, "safe_urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(ValueError, match="大小限制"):
        image_loader.load_image("https://image.civitai.com/image.png", max_bytes=4)
