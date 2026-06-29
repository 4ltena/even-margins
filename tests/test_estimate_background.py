from PIL import Image
from trim import estimate_background


def test_white_background_with_center_shape():
    img = Image.new("RGB", (100, 100), (255, 255, 255))
    # 中央に黒い四角（四隅には影響しない）
    for x in range(40, 60):
        for y in range(40, 60):
            img.putpixel((x, y), (0, 0, 0))
    assert estimate_background(img, corner_size=8) == (255, 255, 255)


def test_dark_background():
    img = Image.new("RGB", (50, 50), (10, 20, 30))
    assert estimate_background(img, corner_size=8) == (10, 20, 30)
