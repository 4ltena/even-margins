from PIL import Image
from trim import _image_signature, is_new_content


def _img(color):
    return Image.new("RGB", (10, 10), color)


def test_signature_equal_for_equal_images():
    assert _image_signature(_img((10, 20, 30))) == _image_signature(_img((10, 20, 30)))


def test_signature_differs_for_different_images():
    assert _image_signature(_img((0, 0, 0))) != _image_signature(_img((255, 255, 255)))


def test_is_new_content_false_for_none():
    assert is_new_content(None, None) is False


def test_is_new_content_skips_own_output():
    out = _img((123, 45, 67))
    sig = _image_signature(out)
    # Identical to the image we just wrote back -> do not re-process
    assert is_new_content(out, sig) is False


def test_is_new_content_accepts_fresh_image():
    out = _img((123, 45, 67))
    sig = _image_signature(out)
    fresh = _img((1, 2, 3))
    assert is_new_content(fresh, sig) is True


def test_is_new_content_true_when_no_previous_output():
    assert is_new_content(_img((9, 9, 9)), None) is True
