import os
from datetime import datetime
from sqlalchemy.orm import Session
from models import Receipt, ReceiptItem
from services.ocr_service import get_ocr_service
from services.parsing_service import get_parsing_service
from services.stock_service import get_stock_service, get_prediction_service
from typing import List, Dict, Tuple

class ReceiptService:
    """レシート処理サービス - OCRから在庫更新までのワークフロー"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ocr_service = get_ocr_service()
        self.parsing_service = get_parsing_service()
        self.stock_service = get_stock_service(db_session)
        self.prediction_service = get_prediction_service(db_session)
    
    def process_receipt(self, image_path: str, store_name: str = None) -> Tuple[Receipt, List[Dict]]:
        """レシート画像を処理して、品目を抽出・在庫に追加
        
        Args:
            image_path: レシート画像のパス
            store_name: 店名（オプション）
        
        Returns:
            (Receipt オブジェクト, 抽出品目リスト)
        """
        # 1. ファイルの存在確認
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"画像ファイル '{image_path}' が見つかりません")
        
        # 2. OCR実行
        print(f"🔍 OCR処理中: {image_path}")
        ocr_text, ocr_results = self.ocr_service.extract_text(image_path)
        
        # 3. 品目解析
        print("📋 品目を解析中...")
        items, raw_text = self.parsing_service.parse_receipt_detailed(ocr_results)
        
        # 4. レシートレコード作成
        receipt = Receipt(
            date=datetime.now(),
            store_name=store_name,
            image_path=image_path,
            ocr_text=ocr_text
        )
        self.db.add(receipt)
        self.db.flush()  # receipt.id を取得するため
        
        # 5. 品目を在庫に追加
        processed_items = []
        for item_info in items:
            # ReceiptItemレコード作成
            receipt_item = ReceiptItem(
                receipt_id=receipt.id,
                item_name=item_info['item_name'],
                quantity=item_info['quantity'],
                price=item_info['price'],
                category=item_info['category']
            )
            self.db.add(receipt_item)
            
            # 在庫に追加
            stock = self.stock_service.add_or_update_stock(
                item_name=item_info['item_name'],
                quantity=item_info['quantity'],
                category=item_info['category']
            )
            
            # 予測を更新
            self.prediction_service.predict_depletion(stock.id)
            
            processed_items.append({
                'item_name': item_info['item_name'],
                'quantity': item_info['quantity'],
                'price': item_info['price'],
                'category': item_info['category']
            })
        
        self.db.commit()
        
        return receipt, processed_items
    
    def get_receipt_by_id(self, receipt_id: int) -> Receipt:
        """レシートを取得"""
        return self.db.query(Receipt).filter_by(id=receipt_id).first()
    
    def get_all_receipts(self, limit: int = 50) -> List[Receipt]:
        """全レシートを取得（最新順）"""
        return self.db.query(Receipt).order_by(Receipt.created_at.desc()).limit(limit).all()
    
    def get_receipt_summary(self) -> Dict:
        """レシート処理の統計情報を取得"""
        receipts = self.db.query(Receipt).all()
        receipt_items = self.db.query(ReceiptItem).all()
        
        total_price = sum(item.price for item in receipt_items if item.price)
        
        return {
            'total_receipts': len(receipts),
            'total_items_recorded': len(receipt_items),
            'total_spent': total_price,
            'unique_items': len(set(item.item_name for item in receipt_items))
        }


def get_receipt_service(db_session: Session) -> ReceiptService:
    """レシートサービスのインスタンスを取得"""
    return ReceiptService(db_session)
