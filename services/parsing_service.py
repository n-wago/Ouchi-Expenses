import re
import pandas as pd
from typing import List, Dict, Tuple

class ParsingService:
    """レシート品目解析サービス"""
    
    # 一般的な日本の支出カテゴリ
    CATEGORIES = {
        '食品': ['米', 'パン', '牛乳', 'チーズ', '卵', '肉', '魚', '野菜', 'フルーツ', 'ジュース', '飲料', 'コーヒー', 'お菓子', 'スナック'],
        '日用雑貨': ['トイレットペーパー', 'ティッシュ', '歯ブラシ', '歯磨き粉', 'シャンプー', 'リンス', 'ボディソープ'],
        '医薬品': ['風邪薬', '胃薬', '鎮痛剤', '常備薬', 'サプリ'],
        '洗剤': ['洗剤', '漂白剤', '柔軟剤', '食器用洗剤'],
        '衛生用品': ['マスク', 'アルコール', '消毒液', '綿棒', 'バンドエイド'],
        '生活用品': ['照明', 'キッチン用品', '布用品'],
    }
    
    @staticmethod
    def categorize_item(item_name: str) -> str:
        """品目名からカテゴリを推測"""
        item_lower = item_name.lower()
        
        for category, keywords in ParsingService.CATEGORIES.items():
            for keyword in keywords:
                if keyword.lower() in item_lower:
                    return category
        
        return 'その他'
    
    @staticmethod
    def extract_price_and_quantity(text: str) -> Tuple[float, float]:
        """テキストから価格と数量を抽出
        
        Returns:
            (price, quantity) タプル
        """
        # 価格パターン（¥や税込表記など）
        price_pattern = r'[¥￥]?\s*(\d{1,5}(?:[,，]\d{3})*(?:\.\d{1,2})?)'
        # 数量パターン（個、本、パック等）
        quantity_pattern = r'(\d+(?:\.\d+)?)\s*(?:個|本|パック|袋|枚|セット|台|組)'
        
        price = None
        quantity = 1.0
        
        # 価格を抽出
        price_match = re.search(price_pattern, text)
        if price_match:
            price_str = price_match.group(1).replace(',', '').replace('，', '')
            try:
                price = float(price_str)
            except ValueError:
                pass
        
        # 数量を抽出
        quantity_match = re.search(quantity_pattern, text)
        if quantity_match:
            try:
                quantity = float(quantity_match.group(1))
            except ValueError:
                pass
        
        return price, quantity
    
    @staticmethod
    def parse_receipt_text(ocr_text: str) -> List[Dict]:
        """OCRテキストからレシート品目を抽出
        
        Args:
            ocr_text: OCRで抽出されたレシートテキスト
        
        Returns:
            品目情報のリスト
        """
        lines = ocr_text.split('\n')
        items = []
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 2:
                continue
            
            # 日本語のみ、または英数字と日本語の混合を対象
            if any('\u4e00' <= c <= '\u9fff' or c.isalnum() for c in line):
                price, quantity = ParsingService.extract_price_and_quantity(line)
                
                # 数字を取り除いて品目名を抽出
                item_name = re.sub(r'[¥￥]?\s*\d{1,5}(?:[,，]\d{3})*(?:\.\d{1,2})?', '', line).strip()
                item_name = re.sub(r'\d+(?:\.\d+)?\s*(?:個|本|パック|袋|枚|セット|台|組)', '', item_name).strip()
                
                if item_name and len(item_name) >= 2:
                    category = ParsingService.categorize_item(item_name)
                    
                    items.append({
                        'item_name': item_name,
                        'quantity': quantity,
                        'price': price,
                        'category': category,
                        'raw_text': line
                    })
        
        return items
    
    @staticmethod
    def parse_receipt_detailed(ocr_results: List[Dict]) -> Tuple[List[Dict], str]:
        """詳細なOCR結果からレシート情報を解析
        
        Args:
            ocr_results: OCRサービスから返された詳細結果
        
        Returns:
            (items_list, raw_text) タプル
        """
        raw_text = '\n'.join([res['text'] for res in ocr_results])
        items = ParsingService.parse_receipt_text(raw_text)
        return items, raw_text


def get_parsing_service():
    """パーシングサービスのインスタンスを取得"""
    return ParsingService()

