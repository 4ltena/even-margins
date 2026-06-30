"""診断用スクリプト（ホットキー・常駐に依存しない）。

使い方:
  1. 余白が不均一な図を Snipping 等でクリップボードにコピーする。
  2. このスクリプトを実行する:  python diagnose.py
  3. 出力をそのまま貼って報告してください。

各境界（クリップボード取得 → 背景推定 → コンテンツ検出 → 整形 → 書き戻し）で
何が起きているかを表示します。
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

    # --- 1. クリップボード取得 ---
    image = trim.grab_clipboard_image()
    if image is None:
        # grabclipboard が何を返したか直接確認
        try:
            from PIL import ImageGrab

            raw = ImageGrab.grabclipboard()
            print(f"[grab] grab_clipboard_image()=None  / ImageGrab.grabclipboard() の型: {type(raw)!r}")
            if isinstance(raw, list):
                print(f"[grab] クリップボードはファイルパスのリストでした: {raw}")
        except Exception as e:
            print(f"[grab] ImageGrab で例外: {e!r}")
        print("=> 画像として取得できていません。ここが原因です。")
        return

    print(f"[grab] OK  mode={image.mode}  size={image.size}")

    rgb = image.convert("RGB")

    # --- 2. 背景色推定 ---
    bg = estimate_background(rgb, corner_size=cfg["corner_size"])
    print(f"[background] 推定背景色={bg}")

    # 四隅の実際の色も表示
    w, h = rgb.size
    px = rgb.load()
    corners = {
        "TL": px[0, 0],
        "TR": px[w - 1, 0],
        "BL": px[0, h - 1],
        "BR": px[w - 1, h - 1],
    }
    print(f"[background] 四隅の実色={corners}")

    # --- 3. コンテンツ検出 ---
    bbox = detect_content_bbox(rgb, bg, tolerance=cfg["tolerance"])
    if bbox is None:
        print(f"[detect] bbox=None  (tolerance={cfg['tolerance']} の範囲内＝全面が背景とみなされた)")
        print("=> 図を検出できていません。tolerance か背景推定が原因の可能性。")
        return
    left, top, right, bottom = bbox
    print(f"[detect] bbox={bbox}  検出図サイズ={right - left}x{bottom - top}  画像全体={w}x{h}")
    print(f"[detect] 元の余白  左={left} 右={w - right} 上={top} 下={h - bottom}")

    # --- 4. 整形 ---
    out = add_uniform_margin(rgb, bbox, cfg["ratio"], bg)
    print(f"[trim] 出力サイズ={out.size}  (入力={image.size})")
    if out.size == image.size:
        print("[trim] 注意: 出力サイズが入力と同一です（既に均等？／検出範囲が全面？）")

    # --- 5. 書き戻し ---
    try:
        trim.set_clipboard_image(out)
        print("[set] クリップボードに書き戻しました。今すぐ貼り付けて確認してください。")
    except Exception as e:
        print(f"[set] 書き戻しで例外: {e!r}")
        print("=> 書き戻し（CF_DIB）が原因です。")
        return

    # 検証: 書き戻した画像を取得し直してサイズ一致を確認
    back = trim.grab_clipboard_image()
    if back is None:
        print("[verify] 書き戻し後に取得し直せませんでした。")
    else:
        print(f"[verify] 書き戻し後のクリップボード画像サイズ={back.size}（期待={out.size}）")
        if back.size == out.size:
            print("=> 書き戻し成功。logic 側は正常です。")


if __name__ == "__main__":
    sys.exit(main())
