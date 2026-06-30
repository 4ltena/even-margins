"""Diagnostic script (independent of the hotkey/watcher).

Usage:
  1. Copy a figure with uneven margins to the clipboard (e.g. via Snipping).
  2. Run this script:  python diagnose.py
  3. Paste the whole output back when reporting an issue.

It prints what happens at each boundary: clipboard grab -> background estimate
-> content detection -> normalization -> write-back.
"""

import sys

import trim
from trim import (
    estimate_background,
    detect_content_bbox,
    add_uniform_margin,
    load_config,
)


def main():
    cfg = load_config()
    print(f"[config] {cfg}")

    # --- 1. Grab from clipboard ---
    image = trim.grab_clipboard_image()
    if image is None:
        # Inspect what grabclipboard actually returned.
        try:
            from PIL import ImageGrab

            raw = ImageGrab.grabclipboard()
            print(f"[grab] grab_clipboard_image()=None  / ImageGrab.grabclipboard() type: {type(raw)!r}")
            if isinstance(raw, list):
                print(f"[grab] Clipboard held a list of file paths: {raw}")
        except Exception as e:
            print(f"[grab] ImageGrab raised: {e!r}")
        print("=> Could not obtain an image. This is the cause.")
        return

    print(f"[grab] OK  mode={image.mode}  size={image.size}")

    rgb = image.convert("RGB")

    # --- 2. Estimate background ---
    bg = estimate_background(rgb, corner_size=cfg["corner_size"])
    print(f"[background] estimated background={bg}")

    # Show the actual corner colors too.
    w, h = rgb.size
    px = rgb.load()
    corners = {
        "TL": px[0, 0],
        "TR": px[w - 1, 0],
        "BL": px[0, h - 1],
        "BR": px[w - 1, h - 1],
    }
    print(f"[background] corner colors={corners}")

    # --- 3. Detect content ---
    bbox = detect_content_bbox(rgb, bg, tolerance=cfg["tolerance"])
    if bbox is None:
        print(f"[detect] bbox=None  (everything within tolerance={cfg['tolerance']} of the background)")
        print("=> No figure detected. Likely the tolerance or background estimate.")
        return
    left, top, right, bottom = bbox
    print(f"[detect] bbox={bbox}  figure size={right - left}x{bottom - top}  full image={w}x{h}")
    print(f"[detect] original margins  left={left} right={w - right} top={top} bottom={h - bottom}")

    # --- 4. Normalize ---
    out = add_uniform_margin(rgb, bbox, cfg["ratio"], bg)
    print(f"[trim] output size={out.size}  (input={image.size})")
    if out.size == image.size:
        print("[trim] note: output size equals input (already balanced, or content fills the frame?)")

    # --- 5. Write back ---
    try:
        trim.set_clipboard_image(out)
        print("[set] Wrote back to the clipboard. Paste now to check.")
    except Exception as e:
        print(f"[set] write-back raised: {e!r}")
        print("=> The write-back (CF_DIB) is the cause.")
        return

    # Verify: read the clipboard again and confirm the size matches.
    back = trim.grab_clipboard_image()
    if back is None:
        print("[verify] Could not re-grab after write-back.")
    else:
        print(f"[verify] clipboard image size after write-back={back.size} (expected={out.size})")
        if back.size == out.size:
            print("=> Write-back succeeded. The core logic is working.")


if __name__ == "__main__":
    sys.exit(main())
