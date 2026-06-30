# 変更履歴

このプロジェクトの変更履歴をまとめる。書式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に従い、バージョンは [セマンティック バージョニング](https://semver.org/lang/ja/) に従う。

## [0.1.0] — 2026-06-30

クリップボードを監視し、新しい画像が入るたびに上下左右の余白を自動で均等化して書き戻す常駐ツールの初版。スニップするだけで余白がそろい、ホットキー操作はいらない。

### 追加

- クリップボード監視デーモン。画像が入った瞬間に整形して書き戻す（`watch_clipboard`）。
- 四隅から背景色を推定し、許容誤差つきで図の範囲を検出（`estimate_background` / `detect_content_bbox`）。
- 図を短辺 × 比率の余白で全周そろえて中央配置（`add_uniform_margin`）。
- 自分が書き戻した画像をシグネチャとクリップボードのシーケンス番号で除外し、再処理ループを防止。
- `config.toml` による設定（`ratio` / `poll_interval` / `tolerance` / `corner_size`）。
- 各処理段階を確認できる切り分け用スクリプト `diagnose.py`。
