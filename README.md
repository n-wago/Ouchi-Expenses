# OUCHI-EXPENSES: 夫婦で使う家計簿アプリ

Python製の家計管理アプリケーション。レシート画像の自動読み込み、OCR文字起こし、品目の仕分け、在庫管理、消耗スパン予測を実装しています。

## 🎯 機能

- **レシート画像読み込み**: JPG/PNG形式のレシート画像を読み込み
- **OCR文字起こし**: easyocrを使用した高精度な日本語・英語テキスト抽出
- **品目仕分け**: 抽出テキストから品目・数量・価格を自動抽出、カテゴリ分類
- **在庫管理**: レシート品目から在庫を自動追加・更新
- **消費記録**: 実際の消費量を登録し、在庫を更新
- **消耗スパン予測**: 過去の消費履歴から消耗期間を予測
- **購入タイミング提案**: 予測結果に基づいて購入推奨日を提案

## 📁 プロジェクト構成

```
Ouchi-Expenses/
├── app.py                      # メインCLI
├── models.py                   # SQLAlchemyデータベースモデル
├── requirements.txt            # Python依存ライブラリ
├── services/
│   ├── __init__.py
│   ├── ocr_service.py          # OCR機能（easyocr）
│   ├── parsing_service.py      # レシート品目解析
│   ├── stock_service.py        # 在庫・予測管理
│   └── receipt_service.py      # レシート処理ワークフロー
├── utils/                      # ユーティリティ関数（今後拡張）
├── data/
│   └── ouchi_expenses.db       # SQLiteデータベース（自動生成）
└── README.md
```

## 🚀 セットアップ

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

**注**: easyocrは初回実行時にモデルをダウンロード（数百MB）します。

### 2. データベースの初期化

```bash
python app.py init
```

## 📖 使用方法

### コマンドリファレンス

#### 1. レシート処理
```bash
python app.py receipt <画像パス> [--store <店名>]
```

例:
```bash
python app.py receipt receipt.jpg --store セーフウェイ
```

**処理内容**:
- 画像をOCRで文字起こし
- テキストから品目・数量・価格を抽出
- 品目をカテゴリ分類
- 自動で在庫に追加
- 消耗スパン予測を更新

#### 2. 在庫確認
```bash
python app.py stock
```

全在庫を一覧表示します。

#### 3. 消費を記録
```bash
python app.py consume <品目名> <数量> [--notes <メモ>]
```

例:
```bash
python app.py consume 牛乳 1 --notes 朝食用
```

**処理内容**:
- 在庫から消費量を減らす
- 消費ログを記録
- 消耗スパン予測を再計算

#### 4. 購入提案を確認
```bash
python app.py recommend
```

消耗予定が近い品目の購入推奨日を表示します。

## 🗄️ データベーススキーマ

### テーブル一覧

1. **receipts**: レシート情報
   - id, date, total_price, store_name, image_path, ocr_text, created_at

2. **receipt_items**: レシート品目
   - id, receipt_id, item_name, quantity, price, category, created_at

3. **stocks**: 在庫管理
   - id, item_name, category, quantity, unit, last_updated

4. **consumption_logs**: 消費ログ
   - id, stock_id, quantity_consumed, consumption_date, notes

5. **stock_predictions**: 消耗スパン予測
   - id, stock_id, avg_consumption_per_day, predicted_depletion_date, purchase_recommendation_date, confidence_score, buffer_days, updated_at

## 🔧 カテゴリマッピング

自動的に以下のカテゴリに分類されます:
- 食品
- 日用雑貨
- 医薬品
- 洗剤
- 衛生用品
- その他

## 📊 予測ロジック

### 消耗スパン計算
1. 過去30日間の消費ログから消費速度（個/日）を計算
2. 消費履歴がない場合はカテゴリの平均値を使用
3. `現在在庫 ÷ 消費速度` で消耗予定日を計算

### 購入提案
- 消耗予定日から3日前を購入推奨日とします
- 信頼度スコア（0.0~1.0）で予測の確実性を表示

## 🛠️ 今後の拡張予定

- [ ] Streamlitを使用したWebUI
- [ ] 複数ユーザー対応
- [ ] 月別・カテゴリ別の支出分析
- [ ] 予測モデルの機械学習化（Prophet等）
- [ ] 家計簿帳簿の自動生成
- [ ] 複数デバイス間の同期
- [ ] 請求額の自動計算・分割

## 📝 ライセンス

MIT License

## 👥 サポート

問題が発生した場合は、GitHubのIssuesで報告してください。
