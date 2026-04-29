from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{BASE_DIR}/data/ouchi_expenses.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False)

class Receipt(Base):
    """レシート記録"""
    __tablename__ = 'receipts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.now)
    total_price = Column(Float, nullable=True)
    store_name = Column(String(255), nullable=True)
    image_path = Column(String(500))
    ocr_text = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    items = relationship('ReceiptItem', back_populates='receipt', cascade='all, delete-orphan')


class ReceiptItem(Base):
    """レシート品目"""
    __tablename__ = 'receipt_items'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(Integer, ForeignKey('receipts.id'), nullable=False)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Float, default=1.0)
    price = Column(Float, nullable=True)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    receipt = relationship('Receipt', back_populates='items')


class Stock(Base):
    """在庫管理"""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    item_name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=True)
    quantity = Column(Float, default=0.0)
    unit = Column(String(50), default='個')  # 個、本、個など
    last_updated = Column(DateTime, default=datetime.now)
    
    consumption_logs = relationship('ConsumptionLog', back_populates='stock', cascade='all, delete-orphan')
    predictions = relationship('StockPrediction', back_populates='stock', cascade='all, delete-orphan')


class ConsumptionLog(Base):
    """消費記録"""
    __tablename__ = 'consumption_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    quantity_consumed = Column(Float, nullable=False)
    consumption_date = Column(DateTime, default=datetime.now)
    notes = Column(Text, nullable=True)
    
    stock = relationship('Stock', back_populates='consumption_logs')


class StockPrediction(Base):
    """在庫消耗予測"""
    __tablename__ = 'stock_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    avg_consumption_per_day = Column(Float, nullable=True)
    predicted_depletion_date = Column(DateTime, nullable=True)
    purchase_recommendation_date = Column(DateTime, nullable=True)
    confidence_score = Column(Float, default=0.0)  # 0.0 ~ 1.0
    buffer_days = Column(Integer, default=3)  # 購入提案のバッファ日数
    updated_at = Column(DateTime, default=datetime.now)
    
    stock = relationship('Stock', back_populates='predictions')


def init_db():
    """データベースを初期化"""
    Base.metadata.create_all(engine)
    print("✓ データベースを初期化しました")


if __name__ == '__main__':
    init_db()
