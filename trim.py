import io
import logging
import os
import sys
import threading
from collections import Counter
from logging.handlers import RotatingFileHandler
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
    "notify": True,
}

logger = logging.getLogger("even-margins")


def _module_dir():
    """Directory containing this module, used to resolve config and log paths."""
    return os.path.dirname(os.path.abspath(__file__))


def default_config_path():
    """Path to config.toml next to this module (independent of the working directory)."""
    return os.path.join(_module_dir(), "config.toml")


def default_log_path():
    """Path to the log file next to this module (independent of the working directory)."""
    return os.path.join(_module_dir(), "even-margins.log")


def setup_logging(path=None, name="even-margins"):
    """Attach a rotating file handler (and a console handler when a console exists).

    Idempotent: a logger that already has handlers is returned unchanged, so calling
    this more than once never stacks duplicate handlers. Under ``pythonw`` there is no
    console (``sys.stdout is None``), so only the file handler is added.
    """
    lg = logging.getLogger(name)
    if lg.handlers:
        return lg
    if path is None:
        path = default_log_path()
    lg.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    lg.addHandler(file_handler)
    if sys.stdout is not None:
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        lg.addHandler(console)
    return lg


def load_config(path=None):
    """Read config.toml and return a dict with missing keys filled from defaults.

    When ``path`` is None, the file is resolved next to this module (not the current
    working directory), so a resident launch does not depend on where it was started.
    """
    if path is None:
        path = default_config_path()
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(path, "rb") as f:
            loaded = tomllib.load(f)
    except FileNotFoundError:
        return cfg
    except tomllib.TOMLDecodeError as e:
        logger.warning("Failed to parse config.toml; using defaults: %s", e)
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


class AppState:
    """Shared runtime state between the tray menu and the clipboard watcher."""

    def __init__(self, enabled=True, notify=True):
        self.enabled = enabled
        self.notify = notify
        self.stop_event = threading.Event()
        self.last_output_sig = None
        self.last_seq = None

    def toggle_enabled(self):
        self.enabled = not self.enabled

    def toggle_notify(self):
        self.notify = not self.notify


def should_process(state, image):
    """True when processing is enabled and the image is new (not our own output)."""
    return state.enabled and is_new_content(image, state.last_output_sig)


def format_notification(in_size, out_size):
    """Build the toast body, e.g. 'Normalized 1280x720 -> 1344x756'."""
    return f"Normalized {in_size[0]}x{in_size[1]} -> {out_size[0]}x{out_size[1]}"


def watch_clipboard(state, config, notifier=None):
    """Watch the clipboard and auto-normalize margins whenever a new image appears.

    Loops until ``state.stop_event`` is set. The image we write back is excluded by
    both its signature (via ``should_process``) and the clipboard sequence number so
    it is never re-processed. On success, when ``notifier`` is given and
    ``state.notify`` is on, ``notifier`` is called with the formatted message.
    """
    import win32clipboard

    interval = config.get("poll_interval", 0.3)
    logger.info(
        "Watching the clipboard (every %ss). "
        "Snip an image and its margins are normalized automatically.",
        interval,
    )
    while not state.stop_event.is_set():
        try:
            seq = win32clipboard.GetClipboardSequenceNumber()
            if seq != state.last_seq:
                state.last_seq = seq
                image = grab_clipboard_image()
                if should_process(state, image):
                    result = process_image(
                        image,
                        ratio=config["ratio"],
                        tolerance=config["tolerance"],
                        corner_size=config["corner_size"],
                    )
                    if result is None:
                        logger.info("No figure detected")
                    else:
                        set_clipboard_image(result)
                        state.last_output_sig = _image_signature(result)
                        # Our own write bumps the sequence number; refresh it to avoid re-processing.
                        state.last_seq = win32clipboard.GetClipboardSequenceNumber()
                        logger.info("Normalized %s", result.size)
                        if notifier is not None and state.notify:
                            notifier(format_notification(image.size, result.size))
        except Exception as e:  # noqa: BLE001  keep the watcher alive
            logger.error("%s", e)
        state.stop_event.wait(interval)


def main():
    setup_logging()
    config = load_config()
    import tray

    tray.run(config)


if __name__ == "__main__":
    main()
