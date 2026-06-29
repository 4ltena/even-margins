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


def detect_content_bbox(image, background, tolerance=20):
    """背景色から tolerance を超えて異なる画素の bbox を返す。無ければ None。"""
    img = image.convert("RGB")
    w, h = img.size
    px = img.load()
    br, bg, bb = background
    left, top, right, bottom = w, h, 0, 0
    found = False
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            if abs(r - br) > tolerance or abs(g - bg) > tolerance or abs(b - bb) > tolerance:
                found = True
                if x < left:
                    left = x
                if y < top:
                    top = y
                if x > right:
                    right = x
                if y > bottom:
                    bottom = y
    if not found:
        return None
    return (left, top, right + 1, bottom + 1)


def add_uniform_margin(image, bbox, ratio, background):
    """bbox でクロップし、短辺×ratio の余白を全周に均等付与した画像を返す。"""
    img = image.convert("RGB")
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    margin = round(min(cw, ch) * ratio)
    canvas = Image.new("RGB", (cw + 2 * margin, ch + 2 * margin), background)
    canvas.paste(cropped, (margin, margin))
    return canvas
