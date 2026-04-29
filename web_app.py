#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, redirect, url_for, session as flask_session
from werkzeug.utils import secure_filename
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json
from pathlib import Path

from models import init_db, engine, Stock, StockPrediction, Receipt, ReceiptItem
from services import (
    get_receipt_service,
    get_stock_service,
    get_prediction_service,
    get_ocr_service,
    get_parsing_service,
)

# Flask アプリ初期化
app = Flask(__name__)
app.secret_key = 'ouchi-expenses-secret-key-2024'

# ファイルアップロード設定
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'bmp'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# データベース設定
Session = sessionmaker(bind=engine)


def allowed_file(filename):
    """ファイル名が許可されたものか確認"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """ホームページ"""
    session = Session()
    try:
        # 統計情報を取得
        receipt_service = get_receipt_service(session)
        summary = receipt_service.get_receipt_summary()
        
        prediction_service = get_prediction_service(session)
        recommendations = prediction_service.get_purchase_recommendations()
        
        return render_template('index.html', 
                             summary=summary, 
                             recommendations=recommendations[:3])  # 最新3件
    finally:
        session.close()


@app.route('/receipt', methods=['GET', 'POST'])
def receipt():
    """レシート処理ページ"""
    if request.method == 'POST':
        # ファイルアップロード処理
        if 'file' not in request.files:
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        file = request.files['file']
        store_name = request.form.get('store_name', '')
        
        if file.filename == '':
            return jsonify({'error': 'ファイルが選択されていません'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'jpg, png, gif, bmp のみアップロード可能です'}), 400
        
        # ファイルを保存
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], timestamp + filename)
        file.save(filepath)
        
        # OCR + パーシング処理（DB反映なし）
        try:
            ocr_service = get_ocr_service()
            parsing_service = get_parsing_service()
            
            # OCR実行
            ocr_text, ocr_results = ocr_service.extract_text(filepath)
            
            # パーシング実行
            items, raw_text = parsing_service.parse_receipt_detailed(ocr_results)
            
            # セッションに一時保存
            flask_session['receipt_data'] = {
                'filepath': filepath,
                'store_name': store_name,
                'ocr_text': ocr_text,
                'items': items,
                'created_at': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'items_count': len(items),
                'items': items,
                'message': f'✅ OCR処理完了 ({len(items)}個の品目を抽出)'
            })
        except Exception as e:
            return jsonify({'error': f'エラー: {str(e)}'}), 500
    
    return render_template('receipt.html')


@app.route('/receipt/confirm', methods=['GET', 'POST'])
def receipt_confirm():
    """レシート内容確認・編集ページ"""
    if not flask_session.get('receipt_data'):
        return redirect(url_for('receipt'))
    
    if request.method == 'POST':
        receipt_data = flask_session.get('receipt_data')
        store_name = request.form.get('store_name', receipt_data.get('store_name', ''))
        
        # 編集されたアイテムを取得
        items = []
        item_count = int(request.form.get('item_count', 0))
        
        for i in range(item_count):
            item_name = request.form.get(f'item_name_{i}')
            quantity = request.form.get(f'quantity_{i}')
            price = request.form.get(f'price_{i}')
            category = request.form.get(f'category_{i}')
            skip = request.form.get(f'skip_{i}')
            
            # スキップされたアイテムは除外
            if skip:
                continue
            
            try:
                quantity = float(quantity) if quantity else 1.0
                price = float(price) if price else None
            except ValueError:
                continue
            
            if item_name:
                items.append({
                    'item_name': item_name,
                    'quantity': quantity,
                    'price': price,
                    'category': category
                })
        
        # DBに反映
        db_session = Session()
        try:
            # レシート情報を作成
            receipt = Receipt(
                date=datetime.now(),
                store_name=store_name,
                image_path=receipt_data['filepath'],
                ocr_text=receipt_data['ocr_text']
            )
            db_session.add(receipt)
            db_session.flush()
            
            # 品目を追加
            stock_service = get_stock_service(db_session)
            prediction_service = get_prediction_service(db_session)
            
            for item_info in items:
                # ReceiptItemレコード作成
                receipt_item = ReceiptItem(
                    receipt_id=receipt.id,
                    item_name=item_info['item_name'],
                    quantity=item_info['quantity'],
                    price=item_info['price'],
                    category=item_info['category']
                )
                db_session.add(receipt_item)
                
                # 在庫に追加
                stock = stock_service.add_or_update_stock(
                    item_name=item_info['item_name'],
                    quantity=item_info['quantity'],
                    category=item_info['category']
                )
                
                # 予測を更新
                prediction_service.predict_depletion(stock.id)
            
            db_session.commit()
            
            # セッションをクリア
            flask_session.pop('receipt_data', None)
            
            return jsonify({
                'success': True,
                'receipt_id': receipt.id,
                'items_count': len(items),
                'message': f'✅ レシート完全に記録されました (ID: {receipt.id})'
            })
        
        except Exception as e:
            db_session.rollback()
            return jsonify({'error': f'エラー: {str(e)}'}), 500
        finally:
            db_session.close()
    
    # GET時は確認画面を表示
    receipt_data = flask_session.get('receipt_data', {})
    items = receipt_data.get('items', [])
    store_name = receipt_data.get('store_name', '')
    
    return render_template('receipt_confirm.html', 
                         items=items, 
                         store_name=store_name)


@app.route('/stock')
def stock():
    """在庫確認ページ"""
    session = Session()
    try:
        stock_service = get_stock_service(session)
        stocks = stock_service.get_all_stocks()
        
        # 在庫をカテゴリ別にグループ化
        stocks_by_category = {}
        for stock in stocks:
            category = stock.category or 'その他'
            if category not in stocks_by_category:
                stocks_by_category[category] = []
            stocks_by_category[category].append(stock)
        
        return render_template('stock.html', stocks_by_category=stocks_by_category)
    finally:
        session.close()


@app.route('/api/stock/<item_name>')
def get_stock_detail(item_name):
    """在庫詳細情報を取得（API）"""
    session = Session()
    try:
        stock_service = get_stock_service(session)
        stock = stock_service.get_stock(item_name)
        
        if not stock:
            return jsonify({'error': '在庫が見つかりません'}), 404
        
        prediction_service = get_prediction_service(session)
        prediction = session.query(StockPrediction).filter_by(stock_id=stock.id).first()
        
        return jsonify({
            'item_name': stock.item_name,
            'quantity': float(stock.quantity),
            'category': stock.category,
            'unit': stock.unit,
            'last_updated': stock.last_updated.isoformat(),
            'prediction': {
                'consumption_per_day': float(prediction.avg_consumption_per_day) if prediction else None,
                'depletion_date': prediction.predicted_depletion_date.isoformat() if prediction else None,
            } if prediction else None
        })
    finally:
        session.close()


@app.route('/consume', methods=['GET', 'POST'])
def consume():
    """消費記録ページ"""
    session = Session()
    try:
        stock_service = get_stock_service(session)
        
        if request.method == 'POST':
            item_name = request.form.get('item_name')
            quantity = float(request.form.get('quantity', 0))
            notes = request.form.get('notes', '')
            
            if not item_name or quantity <= 0:
                return jsonify({'error': '品目と数量を入力してください'}), 400
            
            try:
                log = stock_service.register_consumption(item_name, quantity, notes)
                
                # 予測を再計算
                prediction_service = get_prediction_service(session)
                stock = session.query(Stock).filter_by(id=log.stock_id).first()
                prediction_service.predict_depletion(stock.id)
                
                return jsonify({
                    'success': True,
                    'message': f'✅ {item_name}: {quantity}個を記録しました'
                })
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        
        stocks = stock_service.get_all_stocks()
        return render_template('consume.html', stocks=stocks)
    finally:
        session.close()


@app.route('/recommend')
def recommend():
    """購入提案ページ"""
    session = Session()
    try:
        prediction_service = get_prediction_service(session)
        recommendations = prediction_service.get_purchase_recommendations()
        
        return render_template('recommend.html', recommendations=recommendations)
    finally:
        session.close()


@app.errorhandler(404)
def not_found(e):
    """404エラーハンドラ"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """500エラーハンドラ"""
    return render_template('500.html'), 500


if __name__ == '__main__':
    # データベース初期化
    init_db()
    
    # Flask サーバー起動
    app.run(debug=True, host='0.0.0.0', port=5000)
