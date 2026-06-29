from PIL import Image
from trim import process_image, detect_content_bbox, estimate_background


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


def test_margins_equal_on_all_sides_by_measurement():
    img = Image.new("RGB", (120, 120), (255, 255, 255))
    # 非対称に寄せた図
    for x in range(15, 55):
        for y in range(25, 75):
            img.putpixel((x, y), (0, 0, 0))
    out = process_image(img, ratio=0.1, tolerance=20, corner_size=8)
    w, h = out.size
    bg = estimate_background(out, corner_size=8)
    left, top, right, bottom = detect_content_bbox(out, bg, tolerance=20)
    # 左余白==右余白, 上余白==下余白 (right/bottom は排他なので余白は w-right, h-bottom)
    assert left == w - right
    assert top == h - bottom


def test_content_touching_edge():
    img = Image.new("RGB", (60, 60), (255, 255, 255))
    # 図が左上端に接する (30x40)
    for x in range(0, 30):
        for y in range(0, 40):
            img.putpixel((x, y), (0, 0, 0))
    out = process_image(img, ratio=0.1, tolerance=20, corner_size=8)
    assert out is not None
    # 図 30x40, margin=round(min(30,40)*0.1)=3 -> 36x46
    assert out.size == (36, 46)
