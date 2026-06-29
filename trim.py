import io
import sys
from collections import Counter
from PIL import Image, ImageGrab

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib


DEFAULT_CONFIG = {
    "ratio": 0.05,
    "hotkey": "ctrl+alt+s",
    "tolerance": 20,
    "corner_size": 8,
}


def load_config(path="config.toml"):
    """config.toml を読み、欠落キーを既定値で補完した dict を返す。"""
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(path, "rb") as f:
            loaded = tomllib.load(f)
    except FileNotFoundError:
        return cfg
    cfg.update({k: loaded[k] for k in DEFAULT_CONFIG if k in loaded})
    return cfg


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


def process_image(image, ratio=0.05, tolerance=20, corner_size=8):
    """クリップボード画像を整形して返す。図が無ければ None。"""
    background = estimate_background(image, corner_size=corner_size)
    bbox = detect_content_bbox(image, background, tolerance=tolerance)
    if bbox is None:
        return None
    return add_uniform_margin(image, bbox, ratio, background)


def grab_clipboard_image():
    """クリップボードの画像を返す。画像でなければ None。"""
    data = ImageGrab.grabclipboard()
    if isinstance(data, Image.Image):
        return data
    return None


def set_clipboard_image(image):
    """画像を CF_DIB 形式でクリップボードに書き戻す。"""
    import win32clipboard

    output = io.BytesIO()
    image.convert("RGB").save(output, "BMP")
    # BMP ファイルヘッダ(14 バイト)を除いた DIB 本体
    dib = output.getvalue()[14:]
    output.close()
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
    finally:
        win32clipboard.CloseClipboard()


def run_once(config):
    """ホットキー押下時の処理本体。例外は握りつぶして常駐を維持する。"""
    try:
        image = grab_clipboard_image()
        if image is None:
            print("[skip] クリップボードに画像がありません")
            return
        result = process_image(
            image,
            ratio=config["ratio"],
            tolerance=config["tolerance"],
            corner_size=config["corner_size"],
        )
        if result is None:
            print("[skip] 図を検出できませんでした")
            return
        set_clipboard_image(result)
        print(f"[ok] 整形完了 {result.size}")
    except Exception as e:  # noqa: BLE001  常駐を落とさない
        print(f"[error] {e}", file=sys.stderr)


def main():
    import keyboard

    config = load_config()
    keyboard.add_hotkey(config["hotkey"], lambda: run_once(config))
    print(f"常駐開始。{config['hotkey']} で整形します。Ctrl+C で終了。")
    keyboard.wait()


if __name__ == "__main__":
    main()
