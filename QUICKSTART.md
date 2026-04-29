# 🚀 クイックスタートガイド

## ステップ1: 環境構築

```bash
# 1. プロジェクトディレクトリに移動
cd Ouchi-Expenses

# 2. 仮想環境を作成（オプション）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
venv\Scripts\activate  # Windows

# 3. 依存ライブラリをインストール
pip install -r requirements.txt
```

**初回実行時の注意**
- easyocrはモデルファイル（数百MB）を自動ダウンロードします
- インターネット接続が必要です

## ステップ2: データベース初期化

```bash
python app.py init
```

## ステップ3: 機能テスト

テスト環境でパーシングと在庫管理をテストできます：

```bash
python test_demo.py
```

このコマンドで以下が実行されます：
- レシート品目の自動解析
- 在庫への追加
- 消費記録
- 消耗スパン予測

## ステップ4: 実運用

### 4-1. レシート画像を処理

```bash
python app.py receipt <レシート画像パス> --store <店名>
```

例：
```bash
python app.py receipt receipt.jpg --store セーフウェイ
```

**処理内容**:
```
🔍 OCR処理中: receipt.jpg
📋 品目を解析中...
✅ レシート処理完了 (ID: 1)
📦 抽出された品目: 8個

【抽出品目一覧】
1. 牛乳
   数量: 1, 価格: ¥198
   カテゴリ: 食品
...
```

### 4-2. 在庫を確認

```bash
python app.py stock
```

現在の在庫一覧が表示されます

### 4-3. 消費を記録

```bash
python app.py consume 牛乳 0.5
```

在庫から消費分を差し引き、消耗スパン予測を更新します

### 4-4. 購入提案を確認

```bash
python app.py recommend
```

消耗予定が近い品目の購入推奨日が表示されます

## 📊 ワークフロー図

```
レシート画像
     ↓
  [OCR処理]  ← easyocr
     ↓
  テキスト抽出
     ↓
  [品目解析]  ← 正規表現パーシング
     ↓
  品目・数量・価格・カテゴリ
     ↓
  [在庫追加]  ← データベース更新
     ↓
  [予測計算]  ← 消費速度から消耗日を算出
     ↓
 購入提案生成
```

## 🎯 よくある使用例

### 例1: 毎日のレシート処理
```bash
# 帰宅してレシートを処理
python app.py receipt receipt_today.jpg --store スーパー

# 帰宅後に消費を記録
python app.py consume 牛乳 0.5

# 次の買い物計画を立てる
python app.py recommend
```

### 例2: 月末の統計確認
現在のバージョンではCLIのみですが、今後Streamlit UIで以下が実装予定です：
- 月別の支出合計
- カテゴリ別の支出比率
- 消費パターン分析

## ⚠️ トラブルシューティング

### 「No module named 'easyocr'」

```bash
pip install easyocr
```

### 「画像ファイルが見つかりません」

- 画像ファイルの絶対パスを指定してください
- または、スクリプトと同じディレクトリに画像を配置してください

```bash
python app.py receipt ./receipt.jpg
```

### OCRの精度が低い場合

- 画像の解像度を上げてください（300dpi以上推奨）
- レシートをスキャナーで取り込むと精度が向上します

### 在庫が見つからないエラー

```bash
# まず在庫を確認
python app.py stock

# 手動でテストデータを追加
python test_demo.py
```

## 📝 今後の拡張予定

- [ ] **Streamlit UI**: ブラウザ上で管理可能に
- [ ] **複数ユーザー対応**: 夫婦でそれぞれアカウント作成
- [ ] **支出分析**: 月別・カテゴリ別の統計
- [ ] **機械学習予測**: Prophet/ARIMAモデルで精度向上
- [ ] **複数デバイス同期**: CloudストレージやAPI連携
- [ ] **自動請求額計算**: 夫婦間での支払い分割

---

**質問がある場合**: README.mdを参照するか、GitHubのIssueで報告してください。
