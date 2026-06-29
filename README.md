# beautiful-trimming

クリップボードの切り抜き画像の上下左右の余白を均等に整える常駐ツール。

## セットアップ

```
pip install -r requirements.txt
```

## 使い方

```
python trim.py
```

常駐後、整えたい画像をクリップボードにコピーした状態で `Ctrl+Alt+S`（既定）を押すと、
余白を均等化した画像がクリップボードに書き戻される。設定は `config.toml` で変更する。
