from PIL import Image
from trim import add_uniform_margin


def test_uniform_margin_dimensions_and_centering():
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    # Figure: width 40 (x=30..70) x height 30 (y=20..50)
    for x in range(30, 70):
        for y in range(20, 50):
            img.putpixel((x, y), (0, 0, 0))
    bbox = (30, 20, 70, 50)
    # short side=30, ratio=0.1 -> margin=3px; final size 46x36
    out = add_uniform_margin(img, bbox, ratio=0.1, background=(255, 255, 255))
    assert out.size == (46, 36)
    # margin is the background color
    assert out.getpixel((0, 0)) == (255, 255, 255)
    # figure starts at (3,3) (its top-left pixel is black)
    assert out.getpixel((3, 3)) == (0, 0, 0)
    # the pixel just inside the margin is still background
    assert out.getpixel((2, 2)) == (255, 255, 255)


def test_zero_ratio_is_pure_crop():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    for x in range(10, 30):
        for y in range(10, 40):
            img.putpixel((x, y), (0, 0, 0))
    bbox = (10, 10, 30, 40)
    out = add_uniform_margin(img, bbox, ratio=0.0, background=(255, 255, 255))
    assert out.size == (20, 30)
