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
    "poll_interval": 0.3,
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
    except tomllib.TOMLDecodeError as e:
        print(f"[warn] config.toml の解析に失敗しました。既定値を使用します: {e}", file=sys.stderr)
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

    with io.BytesIO() as output:
        image.convert("RGB").save(output, "BMP")
        # BMP ファイルヘッダ(14 バイト)を除いた DIB 本体
        dib = output.getvalue()[14:]
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
    finally:
        win32clipboard.CloseClipboard()


def _image_signature(image):
    """画像の同一性判定用シグネチャ（RGB バイト列）。"""
    return image.convert("RGB").tobytes()


def is_new_content(image, last_output_signature):
    """処理対象とすべき新しい画像なら True。

    画像でない（None）か、直前に自分が書き戻した画像と同一なら False。
    自分の出力を再処理して縮み続けるループを防ぐためのガード。
    """
    if image is None:
        return False
    return _image_signature(image) != last_output_signature


def watch_clipboard(config, poll_interval=None):
    """クリップボードを監視し、新しい画像が入るたびに自動で整形して書き戻す。

    スニップ等でクリップボードに画像が入った瞬間に処理するため、ホットキーは不要。
    自分が書き戻した画像はシグネチャとシーケンス番号の両方で除外し、再処理しない。
    """
    import time

    import win32clipboard

    interval = poll_interval if poll_interval is not None else config.get("poll_interval", 0.3)
    last_seq = None
    last_output_sig = None
    print(
        f"クリップボード監視を開始しました（{interval}s 間隔）。"
        "スニップすると自動で余白を均等化します。Ctrl+C で終了。"
    )
    try:
        while True:
            try:
                seq = win32clipboard.GetClipboardSequenceNumber()
                if seq != last_seq:
                    last_seq = seq
                    image = grab_clipboard_image()
                    if is_new_content(image, last_output_sig):
                        result = process_image(
                            image,
                            ratio=config["ratio"],
                            tolerance=config["tolerance"],
                            corner_size=config["corner_size"],
                        )
                        if result is None:
                            print("[skip] 図を検出できませんでした")
                        else:
                            set_clipboard_image(result)
                            last_output_sig = _image_signature(result)
                            # 自分の書き戻しでシーケンス番号が進むため、最新値に更新して再処理を防ぐ
                            last_seq = win32clipboard.GetClipboardSequenceNumber()
                            print(f"[ok] 整形しました {result.size}")
            except Exception as e:  # noqa: BLE001  監視を落とさない
                print(f"[error] {e}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


def main():
    config = load_config()
    watch_clipboard(config)


if __name__ == "__main__":
    main()
