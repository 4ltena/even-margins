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
    pixels = []
    for left, top, right, bottom in boxes:
        region = img.crop((left, top, right, bottom))
        pixels.extend(region.getdata())
    return Counter(pixels).most_common(1)[0][0]
