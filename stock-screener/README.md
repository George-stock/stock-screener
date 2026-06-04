# US Stock Screener

kiri_trader さんのスクリーナーを参考にした個人用 US 株スクリーナーです。

## 構成

```
stock-screener/
├── docs/                  ← GitHub Pages で公開するフォルダ
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   ├── data.json          ← 毎日自動生成
│   └── universe.json      ← 毎日自動生成
├── scripts/
│   └── generate.py        ← データ生成スクリプト
└── .github/workflows/
    └── daily-update.yml   ← GitHub Actions（毎日自動実行）
```

## セットアップ手順

### 1. GitHubにリポジトリを作成

1. https://github.com にログイン
2. 右上の「+」→「New repository」
3. Repository name: `stock-screener`
4. **Public** を選択（GitHub Pages を使うため）
5. 「Create repository」をクリック

### 2. ファイルをアップロード

以下の方法でファイルをアップロードしてください。

**方法A: GitHub のウェブ画面（簡単）**
1. リポジトリページで「uploading an existing file」をクリック
2. このzipの中身を全部ドラッグ＆ドロップ
3. 「Commit changes」をクリック

**方法B: Git コマンド**
```bash
git clone https://github.com/あなたのユーザー名/stock-screener.git
# ファイルをコピーして
git add .
git commit -m "Initial commit"
git push
```

### 3. GitHub Pages を有効化

1. リポジトリの「Settings」タブ
2. 左メニュー「Pages」
3. Source: 「Deploy from a branch」
4. Branch: `main` / `docs` フォルダ を選択
5. 「Save」

数分後に `https://あなたのユーザー名.github.io/stock-screener/` で公開されます。

### 4. 初回データ生成（手動実行）

1. リポジトリの「Actions」タブ
2. 「Daily Stock Screener Update」をクリック
3. 「Run workflow」→「Run workflow」

これで `data.json` と `universe.json` が生成されます。

以降は毎日平日 AM6:00（日本時間）に自動実行されます。

## データソースについて

現在のスクリプトは **yfinance（無料）** でフォールバック動作します。
より正確なデータには **Finviz Elite（月$39.5）** の契約が必要です。

Finviz Elite を使う場合は `scripts/generate.py` の先頭にある設定を変更してください。

## スクリーニング条件

- 前日比 ≥ +5%
- 株価 $0.75〜$300  
- 平均出来高 ≥ 50万株
- 売買代金 ≥ $1M
- RelVol（相対出来高） ≥ 1
- 銘柄RS ≥ 60
- 52週安値から +30%以上
