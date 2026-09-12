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
