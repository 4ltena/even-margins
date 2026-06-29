from PIL import Image
from trim import process_image


def test_end_to_end_balances_margins():
    # 図が左に寄った非対称な余白の画像
    img = Image.new("RGB", (120, 120), (255, 255, 255))
    for x in range(10, 50):
        for y in range(30, 70):
            img.putpixel((x, y), (0, 0, 0))
    out = process_image(img, ratio=0.1, tolerance=20, corner_size=8)
    # 図 40×40, margin=4 → 48×48
    assert out.size == (48, 48)
    # 四辺の余白が均等（全周 background）
    assert out.getpixel((0, 0)) == (255, 255, 255)
    assert out.getpixel((47, 47)) == (255, 255, 255)
    assert out.getpixel((4, 4)) == (0, 0, 0)


def test_returns_none_for_blank():
    img = Image.new("RGB", (50, 50), (255, 255, 255))
    assert process_image(img) is None
