from collections import Counter
from PIL import Image


def estimate_background(image, corner_size=8):
    """四隅の領域から最頻 RGB を背景色として返す。"""
    img = image.convert("RGB")
    w, h = img.size
    cs = max(1, min(corner_size, w, h))
    boxes = [
        (0, 0, cs, cs),
        (w - cs, 0, w, cs),
        (0, h - cs, cs, h),
        (w - cs, h - cs, w, h),
    ]
    px = img.load()
    pixels = []
    for left, top, right, bottom in boxes:
        for y in range(top, bottom):
            for x in range(left, right):
                pixels.append(px[x, y])
    return Counter(pixels).most_common(1)[0][0]
