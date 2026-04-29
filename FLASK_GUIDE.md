# 🌐 Flask Webアプリケーション実行ガイド

## 📋 前提条件

- Python 3.10以上
- `requirements.txt` のライブラリがインストール済み
- データベース初期化済み

## 🚀 実行方法

### 1. 仮想環境を有効化

```bash
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 2. 依存関係をインストール（未インストール時）

```bash
pip install -r requirements.txt
```

### 3. Flask サーバーを起動

```bash
python web_app.py
```

**出力例:**
```
 * Serving Flask app 'web_app'
 * Debug mode: on
 * Running on http://0.0.0.0:5000
 * Press CTRL+C to quit
```

### 4. ブラウザでアクセス

- **ローカル**: http://localhost:5000
- **スマホ（同一ネットワーク）**: http://<PCのIPアドレス>:5000

---

## 📱 iPhone/スマホでアクセス

### 方法1: 同一ネットワーク

1. PCとiPhoneを同一WiFiに接続
2. PCのIPアドレスを確認:
   ```bash
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```
3. iPhoneのブラウザで: `http://<IPアドレス>:5000`

### 方法2: ホームスクリーン追加（PWA機能）

1. ブラウザで `http://localhost:5000` にアクセス
2. 共有ボタン → ホームスクリーンに追加
3. アプリアイコンをタップして起動

---

## 📁 プロジェクト構造

```
web_app.py              # Flaskメインアプリ
├── models.py           # データベースモデル
├── services/           # ビジネスロジック
│   ├── ocr_service.py
│   ├── parsing_service.py
│   ├── stock_service.py
│   └── receipt_service.py
├── templates/          # HTMLテンプレート
│   ├── base.html       # ベースレイアウト
│   ├── index.html      # ホーム
│   ├── receipt.html    # レシート処理
│   ├── stock.html      # 在庫確認
│   ├── consume.html    # 消費記録
│   ├── recommend.html  # 購入提案
│   ├── 404.html        # 404エラー
│   └── 500.html        # 500エラー
├── static/             # 静的ファイル
│   ├── style.css       # カスタムスタイル
│   └── script.js       # JavaScriptユーティリティ
└── uploads/            # アップロード画像（自動作成）
```

---

## 🎨 ページ構成

### ホーム (`/`)
- 統計情報（レシート数、支出額等）
- 近日中の購入提案
- クイックアクションボタン

### レシート処理 (`/receipt`)
- 画像ファイルアップロード
- OCR処理実行
- 抽出品目の表示
- 自動在庫追加

### 在庫確認 (`/stock`)
- カテゴリ別タブビュー
- 在庫数の表示
- 詳細情報モーダル

### 消費記録 (`/consume`)
- ドロップダウンから品目選択
- 消費数量入力（小数点対応）
- メモ入力
- 自動予測更新

### 購入提案 (`/recommend`)
- カード表示/表形式の切り替え
- 色別の緊急度表示
- 信頼度スコア表示
- アルゴリズム説明

---

## ⚙️ 環境変数設定（オプション）

`.env` ファイルを作成:

```env
FLASK_DEBUG=True
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=16777216
```

---

## 🔧 デバッグモード

デバッグモードを有効/無効に変更:

**web_app.py の最後:**
```python
if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

- `debug=True`: ホットリロード、詳細エラー表示有効
- `debug=False`: 本番環境用

---

## 📊 ログ確認

### OCR処理ログ
```bash
# ターミナルに出力される
読み込み中…
✓ データベースを初期化しました
```

### エラーログ
```bash
# エラーが発生した場合
ERROR in app.request_handling: ...
```

---

## 🌐 本番環境へのデプロイ

### Railway へのデプロイ例

1. **requirements.txt を確認**
   ```bash
   pip freeze > requirements.txt
   ```

2. **Procfile を作成**
   ```
   web: python web_app.py
   ```

3. **GitHub にpush**
   ```bash
   git add .
   git commit -m "Add Flask web app"
   git push origin main
   ```

4. **Railway で新しいプロジェクト作成**
   - GitHub リポジトリを接続
   - 環境変数を設定
   - デプロイ開始

**アクセスURL**: `https://ouchi-expenses.up.railway.app`

---

### Render へのデプロイ例

1. **render.yaml を作成**
   ```yaml
   services:
     - type: web
       name: ouchi-expenses
       env: python
       plan: free
       buildCommand: pip install -r requirements.txt
       startCommand: python web_app.py
   ```

2. **Render Dashboard** から Git リポジトリを接続

---

## 🐛 トラブルシューティング

### ポート 5000 が使用中

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### ファイルアップロード失敗

- `uploads/` ディレクトリが存在するか確認
- ファイルサイズが16MBを超えていないか確認
- 画像形式がサポートされているか確認（JPG, PNG, GIF, BMP）

### OCR処理が遅い

- 初回実行時はモデルをダウンロード（数分かかる）
- 以降は高速化
- GPU がある場合は easyocr で gpu=True に設定

### CSS/JS が読み込まれない

- `static/` ディレクトリ構造を確認
- ブラウザキャッシュをクリア（Ctrl+Shift+Delete）

### CSRF トークンエラー

- Flask セッションが無効の可能性
- ブラウザのクッキーをクリア
- キャッシュをクリア

---

## 📱 iPhone PWA 設定

### ホームスクリーン追加方法

1. Safari で http://localhost:5000 にアクセス
2. 共有ボタン（↑）をタップ
3. 「ホーム画面に追加」をタップ
4. 名前を確認して「追加」をタップ

### オフライン機能（将来の拡張）

Service Worker を追加することで、オフライン機能が実装可能。

---

## 📞 サポート

問題が発生した場合:
1. ターミナルのエラーメッセージを確認
2. ブラウザの開発者ツール（F12）でネットワークエラーを確認
3. `DEBUG=True` でデバッグモード有効化

---

**実装完了**: Flask + Bootstrap Webアプリケーション
**対応ブラウザ**: Chrome, Safari, Firefox（iOS 14以上推奨）
**レスポンシブ**: iPhone, iPad, Android 対応
