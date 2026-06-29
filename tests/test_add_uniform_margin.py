from PIL import Image
from trim import add_uniform_margin


def test_uniform_margin_dimensions_and_centering():
    img = Image.new("RGB", (200, 200), (255, 255, 255))
    # 図: 幅40(x=30..70) × 高30(y=20..50)
    for x in range(30, 70):
        for y in range(20, 50):
            img.putpixel((x, y), (0, 0, 0))
    bbox = (30, 20, 70, 50)
    # 短辺=30, ratio=0.1 → margin=3px。最終サイズ 46×36
    out = add_uniform_margin(img, bbox, ratio=0.1, background=(255, 255, 255))
    assert out.size == (46, 36)
    # 余白は背景色
    assert out.getpixel((0, 0)) == (255, 255, 255)
    # 図は (3,3) から始まる（左上の図画素は黒）
    assert out.getpixel((3, 3)) == (0, 0, 0)
    # 余白部分（margin 内側直前）は背景色
    assert out.getpixel((2, 2)) == (255, 255, 255)


def test_zero_ratio_is_pure_crop():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    for x in range(10, 30):
        for y in range(10, 40):
            img.putpixel((x, y), (0, 0, 0))
    bbox = (10, 10, 30, 40)
    out = add_uniform_margin(img, bbox, ratio=0.0, background=(255, 255, 255))
    assert out.size == (20, 30)
