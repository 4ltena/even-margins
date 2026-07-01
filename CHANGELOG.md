# 変更履歴

このプロジェクトの変更履歴をまとめる。書式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に従い、バージョンは [セマンティック バージョニング](https://semver.org/lang/ja/) に従う。

## [Unreleased]

### 追加

- タスクトレイ常駐。アイコンのメニューから監視の有効・無効（Enabled）と通知の有無（Notifications）を切り替え、Quit で終了する（`tray.py`）。監視は別スレッド、トレイUIはメインスレッドで動く。
- 整形に成功するたび Windows のトースト通知を表示。`config.toml` の `notify`（既定 `true`）で切り替える。無効時・図が見つからないとき・エラー時は通知しない。
- 稼働ログを `trim.py` と同じ場所の `even-margins.log` に出力（ローテーション付き）。`pythonw` 起動でコンソールが無くても動作を追える。

### 変更

- `config.toml` と `even-margins.log` を `trim.py` と同じディレクトリから解決するようにし、起動時の作業ディレクトリ依存をなくした。どこから起動しても設定とログの場所が変わらない。

## [0.1.0] — 2026-06-30

クリップボードを監視し、新しい画像が入るたびに上下左右の余白を自動で均等化して書き戻す常駐ツールの初版。スニップするだけで余白がそろい、ホットキー操作はいらない。

### 追加

- クリップボード監視デーモン。画像が入った瞬間に整形して書き戻す（`watch_clipboard`）。
- 四隅から背景色を推定し、許容誤差つきで図の範囲を検出（`estimate_background` / `detect_content_bbox`）。
- 図を短辺 × 比率の余白で全周そろえて中央配置（`add_uniform_margin`）。
- 自分が書き戻した画像をシグネチャとクリップボードのシーケンス番号で除外し、再処理ループを防止。
- `config.toml` による設定（`ratio` / `poll_interval` / `tolerance` / `corner_size`）。
- 各処理段階を確認できる切り分け用スクリプト `diagnose.py`。
