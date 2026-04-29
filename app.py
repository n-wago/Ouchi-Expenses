#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import sessionmaker

from models import init_db, engine, Stock
from services import (
    get_receipt_service,
    get_stock_service,
    get_prediction_service,
)

# データベースセッションの準備
Session = sessionmaker(bind=engine)


def init_command(args):
    """データベースを初期化"""
    print("🗄️  データベースを初期化します...")
    init_db()
    print("✅ 初期化完了")


def process_receipt_command(args):
    """レシート画像を処理"""
    session = Session()
    try:
        receipt_service = get_receipt_service(session)
        
        print(f"📸 レシート処理中: {args.image}")
        receipt, items = receipt_service.process_receipt(
            image_path=args.image,
            store_name=args.store
        )
        
        print(f"\n✅ レシート処理完了 (ID: {receipt.id})")
        print(f"📦 抽出された品目: {len(items)}個\n")
        
        print("【抽出品目一覧】")
        print("-" * 70)
        for i, item in enumerate(items, 1):
            print(f"{i}. {item['item_name']}")
            print(f"   数量: {item['quantity']}, 価格: ¥{item['price'] if item['price'] else 'N/A'}")
            print(f"   カテゴリ: {item['category']}")
        print("-" * 70)
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


def stock_command(args):
    """在庫を表示"""
    session = Session()
    try:
        stock_service = get_stock_service(session)
        stocks = stock_service.get_all_stocks()
        
        if not stocks:
            print("在庫がありません")
            return
        
        print("\n【在庫一覧】")
        print("-" * 80)
        print(f"{'品目名':<20} {'カテゴリ':<15} {'在庫数':<10} {'単位':<5} {'最終更新':<20}")
        print("-" * 80)
        
        for stock in stocks:
            print(f"{stock.item_name:<20} {stock.category or 'N/A':<15} {stock.quantity:<10.1f} {stock.unit:<5} {stock.last_updated.strftime('%Y-%m-%d %H:%M'):<20}")
        
        print("-" * 80)
        print(f"合計品目数: {len(stocks)}")
        
    finally:
        session.close()


def consume_command(args):
    """消費を記録"""
    session = Session()
    try:
        stock_service = get_stock_service(session)
        
        log = stock_service.register_consumption(
            item_name=args.item,
            quantity_consumed=args.quantity,
            notes=args.notes
        )
        
        stock = session.query(Stock).filter_by(id=log.stock_id).first()
        print(f"✅ 消費を記録しました")
        print(f"品目: {stock.item_name}")
        print(f"消費量: {log.quantity_consumed} {stock.unit}")
        print(f"残在庫: {stock.quantity} {stock.unit}")
        
        # 予測を再計算
        prediction_service = get_prediction_service(session)
        prediction_service.predict_depletion(stock.id)
        
    except Exception as e:
        print(f"❌ エラー: {str(e)}")
        sys.exit(1)
    finally:
        session.close()


def recommend_command(args):
    """購入提案を表示"""
    session = Session()
    try:
        prediction_service = get_prediction_service(session)
        recommendations = prediction_service.get_purchase_recommendations()
        
        if not recommendations:
            print("現在、購入提案がありません")
            return
        
        print("\n【購入提案】")
        print("-" * 100)
        print(f"{'品目名':<20} {'カテゴリ':<15} {'現在庫':<10} {'消費速度':<15} {'消耗予定':<20} {'購入推奨日':<20} {'信頼度':<10}")
        print("-" * 100)
        
        for rec in recommendations:
            confidence_pct = f"{rec['confidence']*100:.0f}%"
            depletion_str = rec['depletion_date'].strftime('%Y-%m-%d') if rec['depletion_date'] else 'N/A'
            recommend_str = rec['recommend_purchase_by'].strftime('%Y-%m-%d') if rec['recommend_purchase_by'] else 'N/A'
            consumption_str = f"{rec['consumption_per_day']:.2f}/日" if rec['consumption_per_day'] else 'N/A'
            
            print(f"{rec['item_name']:<20} {rec['category']:<15} {rec['current_quantity']:<10.1f} {consumption_str:<15} {depletion_str:<20} {recommend_str:<20} {confidence_pct:<10}")
        
        print("-" * 100)
        
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(
        description='OUCHI-EXPENSES: 夫婦で使う家計簿アプリ',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='コマンド')
    
    # init コマンド
    subparsers.add_parser('init', help='データベースを初期化')
    
    # receipt コマンド
    receipt_parser = subparsers.add_parser('receipt', help='レシート画像を処理')
    receipt_parser.add_argument('image', help='レシート画像のパス')
    receipt_parser.add_argument('--store', help='店名（オプション）')
    
    # stock コマンド
    subparsers.add_parser('stock', help='在庫一覧を表示')
    
    # consume コマンド
    consume_parser = subparsers.add_parser('consume', help='消費を記録')
    consume_parser.add_argument('item', help='品目名')
    consume_parser.add_argument('quantity', type=float, help='消費数量')
    consume_parser.add_argument('--notes', help='メモ（オプション）')
    
    # recommend コマンド
    subparsers.add_parser('recommend', help='購入提案を表示')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # コマンド実行
    if args.command == 'init':
        init_command(args)
    elif args.command == 'receipt':
        process_receipt_command(args)
    elif args.command == 'stock':
        stock_command(args)
    elif args.command == 'consume':
        consume_command(args)
    elif args.command == 'recommend':
        recommend_command(args)


if __name__ == '__main__':
    main()