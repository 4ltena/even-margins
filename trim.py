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
    """Read config.toml and return a dict with missing keys filled from defaults."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(path, "rb") as f:
            loaded = tomllib.load(f)
    except FileNotFoundError:
        return cfg
    except tomllib.TOMLDecodeError as e:
        print(f"[warn] Failed to parse config.toml; using defaults: {e}", file=sys.stderr)
        return cfg
    cfg.update({k: loaded[k] for k in DEFAULT_CONFIG if k in loaded})
    return cfg


def estimate_background(image, corner_size=8):
    """Return the most common RGB color sampled from the four corners as the background."""
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
    """Return the bbox of pixels differing from the background beyond tolerance, or None."""
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
    """Crop to bbox and return it centered on a canvas with an equal margin on all sides."""
    img = image.convert("RGB")
    cropped = img.crop(bbox)
    cw, ch = cropped.size
    margin = round(min(cw, ch) * ratio)
    canvas = Image.new("RGB", (cw + 2 * margin, ch + 2 * margin), background)
    canvas.paste(cropped, (margin, margin))
    return canvas


def process_image(image, ratio=0.05, tolerance=20, corner_size=8):
    """Normalize a clipboard image and return the result, or None if no content is found."""
    background = estimate_background(image, corner_size=corner_size)
    bbox = detect_content_bbox(image, background, tolerance=tolerance)
    if bbox is None:
        return None
    return add_uniform_margin(image, bbox, ratio, background)


def grab_clipboard_image():
    """Return the clipboard image, or None if the clipboard does not hold an image."""
    data = ImageGrab.grabclipboard()
    if isinstance(data, Image.Image):
        return data
    return None


def set_clipboard_image(image):
    """Write the image back to the clipboard as CF_DIB."""
    import win32clipboard

    with io.BytesIO() as output:
        image.convert("RGB").save(output, "BMP")
        # DIB body: the BMP file header (14 bytes) is stripped off.
        dib = output.getvalue()[14:]
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, dib)
    finally:
        win32clipboard.CloseClipboard()


def _image_signature(image):
    """Return an identity signature (RGB byte string) used to compare images."""
    return image.convert("RGB").tobytes()


def is_new_content(image, last_output_signature):
    """Return True if the image should be processed.

    Returns False when there is no image (None) or when it is identical to the
    image we just wrote back. This guards against re-processing our own output
    in a loop, which would otherwise keep shrinking the figure.
    """
    if image is None:
        return False
    return _image_signature(image) != last_output_signature


def watch_clipboard(config, poll_interval=None):
    """Watch the clipboard and auto-normalize margins whenever a new image appears.

    Because processing happens the moment an image lands on the clipboard (e.g.
    right after a snip), no hotkey is needed. The image we write back is excluded
    by both its signature and the clipboard sequence number so it is never
    re-processed.
    """
    import time

    import win32clipboard

    interval = poll_interval if poll_interval is not None else config.get("poll_interval", 0.3)
    last_seq = None
    last_output_sig = None
    print(
        f"Watching the clipboard (every {interval}s). "
        "Snip an image and its margins are normalized automatically. Press Ctrl+C to quit."
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
                            print("[skip] No figure detected")
                        else:
                            set_clipboard_image(result)
                            last_output_sig = _image_signature(result)
                            # Our own write bumps the sequence number; refresh it to avoid re-processing.
                            last_seq = win32clipboard.GetClipboardSequenceNumber()
                            print(f"[ok] Normalized {result.size}")
            except Exception as e:  # noqa: BLE001  keep the watcher alive
                print(f"[error] {e}", file=sys.stderr)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass


def main():
    config = load_config()
    watch_clipboard(config)


if __name__ == "__main__":
    main()
