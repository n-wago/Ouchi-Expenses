#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テストスクリプト: OCRと在庫管理の機能確認
実際のレシート画像がない場合でも、パーシング機能をテストできます
"""

from sqlalchemy.orm import sessionmaker
from models import init_db, engine, Stock
from services import (
    get_parsing_service,
    get_stock_service,
    get_prediction_service,
)

Session = sessionmaker(bind=engine)

def test_parsing():
    """パーシング機能のテスト"""
    print("=" * 70)
    print("📋 【テスト1】レシート品目解析")
    print("=" * 70)
    
    # サンプルレシートテキスト
    sample_receipt = """
    セーフウェイ
    2024年4月22日 10:30
    
    牛乳 1L          ¥198
    食パン           ¥189
    卵 10個          ¥298
    トマト           ¥95
    
    トイレットペーパー
    12ロール         ¥890
    
    歯ブラシ         ¥199
    シャンプー       ¥598
    
    風邪薬           ¥980
    
    合計             ¥3,448
    """
    
    parsing_service = get_parsing_service()
    items = parsing_service.parse_receipt_text(sample_receipt)
    
    print(f"\n抽出されたアイテム数: {len(items)}\n")
    print(f"{'#':<3} {'品目名':<20} {'数量':<10} {'価格':<10} {'カテゴリ':<15}")
    print("-" * 70)
    
    for i, item in enumerate(items, 1):
        price_str = f"¥{int(item['price'])}" if item['price'] else "N/A"
        print(f"{i:<3} {item['item_name']:<20} {item['quantity']:<10.1f} {price_str:<10} {item['category']:<15}")
    
    print("-" * 70)
    return items


def test_stock_management():
    """在庫管理機能のテスト"""
    print("\n" + "=" * 70)
    print("📦 【テスト2】在庫追加・更新")
    print("=" * 70 + "\n")
    
    session = Session()
    stock_service = get_stock_service(session)
    
    # テストデータ作成
    test_items = [
        ('牛乳', 2, '食品'),
        ('食パン', 1, '食品'),
        ('卵', 2, '食品'),
        ('トイレットペーパー', 1, '日用雑貨'),
        ('歯ブラシ', 1, '日用雑貨'),
        ('シャンプー', 1, '日用雑貨'),
    ]
    
    print("在庫に品目を追加中...\n")
    for item_name, qty, category in test_items:
        stock = stock_service.add_or_update_stock(
            item_name=item_name,
            quantity=qty,
            category=category
        )
        print(f"✓ {item_name}: {qty}個 ({category})")
    
    # 在庫確認
    stocks = stock_service.get_all_stocks()
    print(f"\n現在の在庫数: {len(stocks)}\n")
    print(f"{'品目名':<20} {'数量':<10} {'カテゴリ':<15}")
    print("-" * 70)
    for stock in stocks:
        print(f"{stock.item_name:<20} {stock.quantity:<10.1f} {stock.category:<15}")
    
    session.close()
    return stocks


def test_consumption_and_prediction():
    """消費記録と予測のテスト"""
    print("\n" + "=" * 70)
    print("📊 【テスト3】消費記録と予測")
    print("=" * 70 + "\n")
    
    session = Session()
    stock_service = get_stock_service(session)
    prediction_service = get_prediction_service(session)
    
    # 消費を記録（複数日にわたる）
    print("消費を記録中...\n")
    
    consumption_data = [
        ('牛乳', 0.5, '朝飲んだ'),
        ('卵', 2, '朝食用'),
        ('食パン', 0.5, '朝食用'),
    ]
    
    for item_name, qty, notes in consumption_data:
        log = stock_service.register_consumption(
            item_name=item_name,
            quantity_consumed=qty,
            notes=notes
        )
        stock = session.query(Stock).filter_by(id=log.stock_id).first()
        print(f"✓ {item_name}: {qty}個消費 (残: {stock.quantity}個)")
    
    # 予測を更新
    print("\n消耗スパン予測を計算中...\n")
    stocks = stock_service.get_all_stocks()
    for stock in stocks:
        prediction = prediction_service.predict_depletion(stock.id, min_history_days=1)
        if prediction:
            consumption_str = f"{prediction.avg_consumption_per_day:.2f}個/日" if prediction.avg_consumption_per_day else "N/A"
            depletion_str = prediction.predicted_depletion_date.strftime('%Y-%m-%d') if prediction.predicted_depletion_date else "N/A"
            print(f"✓ {stock.item_name}")
            print(f"  消費速度: {consumption_str}")
            print(f"  消耗予定: {depletion_str}")
            print(f"  信頼度: {prediction.confidence_score*100:.0f}%")
    
    # 購入提案
    print("\n【購入提案】")
    print("-" * 70)
    recommendations = prediction_service.get_purchase_recommendations()
    
    if recommendations:
        for rec in recommendations:
            recommend_str = rec['recommend_purchase_by'].strftime('%Y-%m-%d') if rec['recommend_purchase_by'] else 'N/A'
            print(f"✓ {rec['item_name']}: {recommend_str}までに購入を推奨")
    else:
        print("購入提案はありません")
    
    print("-" * 70)
    session.close()


def main():
    """全テストを実行"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  OUCHI-EXPENSES テストスイート".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝\n")
    
    try:
        # データベース初期化
        print("🗄️  データベースを初期化中...\n")
        init_db()
        
        # テスト実行
        test_parsing()
        test_stock_management()
        test_consumption_and_prediction()
        
        print("\n" + "=" * 70)
        print("✅ 全テスト完了")
        print("=" * 70)
        print("\n次のステップ:")
        print("1. レシート画像を用意します")
        print("2. `python app.py receipt <画像パス> --store <店名>` で処理します")
        print("3. `python app.py stock` で在庫を確認します")
        print("4. `python app.py recommend` で購入提案を確認します\n")
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
