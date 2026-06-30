from PIL import Image
from trim import detect_content_bbox


def test_detects_centered_shape():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    for x in range(30, 70):
        for y in range(20, 50):
            img.putpixel((x, y), (0, 0, 0))
    # bbox is (30, 20, 70, 50) (right/bottom exclusive)
    assert detect_content_bbox(img, (255, 255, 255), tolerance=20) == (30, 20, 70, 50)


def test_returns_none_for_uniform_image():
    img = Image.new("RGB", (40, 40), (255, 255, 255))
    assert detect_content_bbox(img, (255, 255, 255), tolerance=20) is None


def test_tolerance_ignores_near_background_noise():
    img = Image.new("RGB", (40, 40), (255, 255, 255))
    # Noise close to the background (diff 10 < tolerance 20) is ignored
    img.putpixel((5, 5), (245, 245, 245))
    # Only the clear figure (large diff) is detected
    img.putpixel((20, 20), (0, 0, 0))
    assert detect_content_bbox(img, (255, 255, 255), tolerance=20) == (20, 20, 21, 21)
