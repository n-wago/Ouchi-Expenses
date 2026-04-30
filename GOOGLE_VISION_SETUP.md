# Google Cloud Vision API セットアップガイド

## 🚀 概要

このプロジェクトは、**Google Cloud Vision API** を使用した高精度な OCR システムに移行しました。

**easyocr** の精度が低かったため、Google の高度な機械学習モデルを採用しました。

### 精度の改善期待値
- **easyocr**: 日本語レシート認識 60-70%
- **Vision API**: 日本語レシート認識 95%+

---

## 📋 セットアップステップ (5-10 分)

### ステップ 1: GCP プロジェクトを作成

1. **Google Cloud Console にアクセス**
   ```
   https://console.cloud.google.com/
   ```

2. **プロジェクトを新規作成**
   - 画面上部の「プロジェクト選択」をクリック
   - 「新しいプロジェクト」をクリック
   - プロジェクト名: `ouchi-expenses`
   - 「作成」をクリック (2分待つ)

---

### ステップ 2: Vision API を有効化

1. **API ライブラリへ移動**
   ```
   左メニュー > API とサービス > ライブラリ
   ```

2. **Cloud Vision API を検索**
   - 検索ボックスに `cloud vision` と入力
   - 「Cloud Vision API」をクリック
   - 「有効にする」をクリック (1分待つ)

---

### ステップ 3: サービスアカウントを作成

1. **認証情報ページへ移動**
   ```
   左メニュー > API とサービス > 認証情報
   ```

2. **新しいサービスアカウントを作成**
   - 「+ 認証情報を作成」をクリック
   - 「サービスアカウント」を選択
   - サービスアカウント名: `ouchi-expenses-app`
   - 「作成して続行」をクリック

3. **ロール（権限）を設定**
   - 「ロールを選択」フィールドをクリック
   - 「Cloud Vision API」を検索
   - 「Cloud Vision API 編集者」を選択
   - 「続行」をクリック
   - 「完了」をクリック

---

### ステップ 4: JSON キーファイルをダウンロード

1. **作成したサービスアカウントをクリック**
   - サービスアカウント一覧から `ouchi-expenses-app` をクリック

2. **キータブでキーを作成**
   - 「キー」タブをクリック
   - 「キーを追加」をクリック
   - 「新しいキーを作成」をクリック
   - 「JSON」を選択
   - 「作成」をクリック

3. **ダウンロードされたファイルを保存**
   - ファイル名: `google-cloud-key.json`
   - 保存先:
     ```
     c:\Users\USER\OneDrive\ドキュメント\Ouchi-Expenses\config\google-cloud-key.json
     ```

   ⚠️ **重要**: このファイルはプロジェクトの認証情報を含むため、絶対に Git にコミットしないでください。
   `.gitignore` に自動的に除外されています。

---

### ステップ 5: Python パッケージをインストール

1. **ターミナルで以下を実行**
   ```bash
   cd "c:\Users\USER\OneDrive\ドキュメント\Ouchi-Expenses"
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   ⏱️ **初回は 3-5 分かかります** (google-cloud-vision は大きめのパッケージ)

2. **インストール確認**
   ```bash
   python -c "from google.cloud import vision; print('✅ Vision API がインストールされました')"
   ```

---

## ✅ セットアップ完了の確認

### 方法 1: Python コードで確認

```bash
python
```

```python
from services.ocr_service import get_ocr_service

# OCR サービスを初期化
ocr = get_ocr_service()
print("✅ OCR サービスが正常に初期化されました")
```

### 方法 2: テスト画像で確認

1. **テスト画像を用意** (レシートやテキスト含む画像)
   ```bash
   # test.jpg をプロジェクトルートに配置
   ```

2. **以下を実行**
   ```python
   from services.ocr_service import get_ocr_service
   
   ocr = get_ocr_service()
   text, results = ocr.extract_text('test.jpg')
   
   print("抽出テキスト:")
   print(text)
   print(f"\n検出単語数: {len(results)}")
   ```

---

## 🔧 トラブルシューティング

### ❌ エラー: `credentials_path` が見つからない

**原因**: `google-cloud-key.json` がダウンロードされていません

**解決**:
1. ステップ 4 を再度実行
2. ファイルが正確に以下に配置されていることを確認:
   ```
   config/google-cloud-key.json
   ```

### ❌ エラー: `google.cloud.vision` がインストールされていない

**原因**: パッケージがインストールされていません

**解決**:
```bash
pip install google-cloud-vision==3.7.4
```

### ❌ エラー: 認証に失敗した

**原因**: GCP プロジェクトで Vision API が有効化されていません

**解決**:
1. https://console.cloud.google.com/apis/api/vision.googleapis.com
2. 「有効にする」をクリック
3. 数分待機してから再試行

### ❌ エラー: API 割当が超過した

**原因**: 月間 API リクエスト数の上限を超過

**解決**:
- 無料枠: 月 1,000 リクエスト
- Vision API の使用量を確認: https://console.cloud.google.com/apis/dashboard
- 必要に応じて課金を設定

---

## 💰 コスト情報

### Google Cloud Vision API の料金 (2024年時点)

| 用途 | 価格 |
|-----|------|
| 無料枠 | 月 1,000 リクエスト無料 |
| TEXT_DETECTION | $1.50 / 1,000 リクエスト |
| DOCUMENT_TEXT_DETECTION | $1.50 / 1,000 リクエスト |

**例**: 1 日 10 枚のレシート処理
- 月: 300 リクエスト
- 費用: 無料枠内

---

## 📚 参考資料

- [Google Cloud Vision API ドキュメント](https://cloud.google.com/vision/docs)
- [Python クライアント ライブラリ](https://cloud.google.com/python/docs/reference/vision/latest)
- [テキスト検出ガイド](https://cloud.google.com/vision/docs/ocr)

---

## 🎯 次のステップ

セットアップ完了後:

1. **Flask アプリを起動**
   ```bash
   python web_app.py
   ```

2. **ブラウザで開く**
   ```
   http://localhost:5000
   ```

3. **レシート画像をアップロード**
   - 高精度な OCR 結果を確認

---

**質問または問題がある場合は、このドキュメントを参照してください。**
