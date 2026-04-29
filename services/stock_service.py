from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Stock, ConsumptionLog, StockPrediction, ReceiptItem
import numpy as np
from typing import Optional, List, Dict

class StockService:
    """在庫管理サービス"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def add_or_update_stock(self, item_name: str, quantity: float, category: str = None, unit: str = '個') -> Stock:
        """在庫を追加または更新"""
        stock = self.db.query(Stock).filter_by(item_name=item_name).first()
        
        if stock:
            stock.quantity += quantity
            stock.last_updated = datetime.now()
        else:
            stock = Stock(
                item_name=item_name,
                category=category,
                quantity=quantity,
                unit=unit
            )
            self.db.add(stock)
        
        self.db.commit()
        return stock
    
    def register_consumption(self, item_name: str, quantity_consumed: float, notes: str = None) -> Optional[ConsumptionLog]:
        """消費を記録し、在庫を更新"""
        stock = self.db.query(Stock).filter_by(item_name=item_name).first()
        
        if not stock:
            raise ValueError(f"品目 '{item_name}' が在庫に存在しません")
        
        if stock.quantity < quantity_consumed:
            raise ValueError(f"在庫不足: {item_name} (在庫: {stock.quantity}, 消費: {quantity_consumed})")
        
        # 消費ログを記録
        log = ConsumptionLog(
            stock_id=stock.id,
            quantity_consumed=quantity_consumed,
            notes=notes
        )
        self.db.add(log)
        
        # 在庫を減らす
        stock.quantity -= quantity_consumed
        stock.last_updated = datetime.now()
        
        self.db.commit()
        return log
    
    def get_stock(self, item_name: str) -> Optional[Stock]:
        """在庫情報を取得"""
        return self.db.query(Stock).filter_by(item_name=item_name).first()
    
    def get_all_stocks(self) -> List[Stock]:
        """全在庫を取得"""
        return self.db.query(Stock).all()


class PredictionService:
    """在庫消耗予測サービス"""
    
    # 各カテゴリの平均消耗日数（日数）
    CATEGORY_AVG_CONSUMPTION_DAYS = {
        '食品': 7,
        '日用雑貨': 30,
        '医薬品': 60,
        '洗剤': 30,
        '衛生用品': 14,
        'その他': 30
    }
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_consumption_rate(self, stock_id: int, days: int = 30) -> Optional[float]:
        """過去N日間の消費速度を計算（個/日）"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        logs = self.db.query(ConsumptionLog).filter(
            ConsumptionLog.stock_id == stock_id,
            ConsumptionLog.consumption_date >= cutoff_date
        ).all()
        
        if not logs:
            return None
        
        total_consumed = sum(log.quantity_consumed for log in logs)
        days_with_data = len(set(log.consumption_date.date() for log in logs))
        
        if days_with_data == 0:
            return None
        
        return total_consumed / days_with_data
    
    def predict_depletion(self, stock_id: int, min_history_days: int = 7) -> Optional[StockPrediction]:
        """消耗スパンを予測し、購入タイミングを提案"""
        stock = self.db.query(Stock).filter_by(id=stock_id).first()
        if not stock:
            return None
        
        # 消費速度を計算
        consumption_rate = self.calculate_consumption_rate(stock_id, days=min_history_days)
        
        # 履歴がない場合はカテゴリの平均値を使用
        if consumption_rate is None:
            avg_days = self.CATEGORY_AVG_CONSUMPTION_DAYS.get(stock.category, 30)
            consumption_rate = stock.quantity / avg_days if stock.quantity > 0 else 0.1
            confidence = 0.3  # 低い信頼度
        else:
            confidence = 0.8  # 実績ベースなので高い信頼度
        
        # 消費速度が0以下の場合（消費記録がない）
        if consumption_rate <= 0:
            consumption_rate = 0.1
            confidence = 0.1
        
        # 消耗予測日を計算
        if consumption_rate > 0:
            days_until_empty = stock.quantity / consumption_rate
        else:
            days_until_empty = 999
        
        predicted_depletion = datetime.now() + timedelta(days=days_until_empty)
        
        # 購入提案日（バッファ日数を考慮）
        buffer_days = 3
        purchase_recommendation = predicted_depletion - timedelta(days=buffer_days)
        
        # 予測結果を保存
        prediction = self.db.query(StockPrediction).filter_by(stock_id=stock_id).first()
        
        if prediction:
            prediction.avg_consumption_per_day = consumption_rate
            prediction.predicted_depletion_date = predicted_depletion
            prediction.purchase_recommendation_date = purchase_recommendation
            prediction.confidence_score = confidence
            prediction.updated_at = datetime.now()
        else:
            prediction = StockPrediction(
                stock_id=stock_id,
                avg_consumption_per_day=consumption_rate,
                predicted_depletion_date=predicted_depletion,
                purchase_recommendation_date=purchase_recommendation,
                confidence_score=confidence,
                buffer_days=buffer_days
            )
            self.db.add(prediction)
        
        self.db.commit()
        return prediction
    
    def get_purchase_recommendations(self) -> List[Dict]:
        """購入提案一覧を取得"""
        now = datetime.now()
        
        predictions = self.db.query(StockPrediction).filter(
            StockPrediction.purchase_recommendation_date <= now + timedelta(days=7)
        ).all()
        
        recommendations = []
        for pred in predictions:
            stock = self.db.query(Stock).filter_by(id=pred.stock_id).first()
            if stock:
                recommendations.append({
                    'item_name': stock.item_name,
                    'category': stock.category,
                    'current_quantity': stock.quantity,
                    'consumption_per_day': pred.avg_consumption_per_day,
                    'depletion_date': pred.predicted_depletion_date,
                    'recommend_purchase_by': pred.purchase_recommendation_date,
                    'confidence': pred.confidence_score,
                    'days_until_empty': (pred.predicted_depletion_date - now).days
                })
        
        # 消耗日数でソート（早い順）
        recommendations.sort(key=lambda x: x['recommend_purchase_by'])
        return recommendations


def get_stock_service(db_session: Session) -> StockService:
    """在庫サービスのインスタンスを取得"""
    return StockService(db_session)


def get_prediction_service(db_session: Session) -> PredictionService:
    """予測サービスのインスタンスを取得"""
    return PredictionService(db_session)
