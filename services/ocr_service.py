from google.cloud import vision
from google.oauth2 import service_account
import cv2
import numpy as np
from PIL import Image
import os
from pathlib import Path

class OCRService:
    """Google Cloud Vision API を使用した高精度 OCR サービス"""
    
    def __init__(self, credentials_path=None):
        """初期化 - Google Cloud Vision API クライアントを準備
        
        Args:
            credentials_path: GCP サービスアカウント JSON キーのパス
        """
        # 認証情報のパスを解決
        if credentials_path is None:
            # デフォルト: プロジェクトルート/config/google-cloud-key.json
            project_root = Path(__file__).parent.parent
            credentials_path = project_root / 'config' / 'google-cloud-key.json'
        
        self.credentials_path = str(credentials_path)
        
        # 環境変数をセット
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.credentials_path
        
        # Vision API クライアントを初期化
        self.client = vision.ImageAnnotatorClient(
            credentials=service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
        )
    
    @staticmethod
    def imread_unicode(path):
        """日本語パス対応の画像読み込み"""
        with open(path, 'rb') as f:
            img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
            return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    @staticmethod
    def preprocess_image(image_path, resize_width=1200):
        """画像の前処理（OCR向けに正規化）
        
        Vision API は高品質な画像を好むため、リサイズのみを行う
        """
        img = OCRService.imread_unicode(image_path)
        if img is None:
            raise FileNotFoundError(f"画像ファイル '{image_path}' が見つかりません")
        
        # リサイズ（幅を統一、Vision API に適した高解像度）
        h, w = img.shape[:2]
        if w > resize_width:
            scale = resize_width / w
            new_h = int(h * scale)
            resized = cv2.resize(img, (resize_width, new_h), interpolation=cv2.INTER_LANCZOS4)
        else:
            resized = img
        
        return resized
    
    def extract_text(self, image_path):
        """Google Cloud Vision API を使用してテキストを抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            (extracted_text, detailed_results) タプル
            - extracted_text: 改行区切りのテキスト文字列
            - detailed_results: 信頼度とバウンディングボックス情報を含む辞書のリスト
        """
        try:
            # 画像の前処理（リサイズのみ）
            processed_img = self.preprocess_image(image_path)
            
            # 処理済み画像をファイルに保存（Vision API に送信するため）
            temp_path = image_path.replace('.', '_temp.')
            cv2.imwrite(temp_path, processed_img)
            
            # Vision API 用に画像を読み込み
            with open(temp_path, 'rb') as f:
                image_content = f.read()
            
            # Vision API でテキスト検出（ドキュメント検出で高精度）
            image = vision.Image(content=image_content)
            
            # 1. DOCUMENT_TEXT_DETECTION を使用（複数行テキストに最適）
            response = self.client.document_text_detection(image=image)
            
            # 2. 同時に TEXT_DETECTION も実行（フォールバック用）
            text_response = self.client.text_detection(image=image)
            
            # 結果の解析
            extracted_text = ''
            detailed_results = []
            
            # ドキュメント検出の結果を処理
            if response.full_text_annotation:
                extracted_text = response.full_text_annotation.text
                
                # ページごとの処理
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            for word in paragraph.words:
                                word_text = ''.join([symbol.text for symbol in word.symbols])
                                confidence = word.confidence if word.confidence else 0
                                
                                # バウンディングボックスを取得
                                bbox = [vertex.x for vertex in word.bounding_box.vertices]
                                
                                detailed_results.append({
                                    'text': word_text,
                                    'confidence': confidence,
                                    'bbox': bbox
                                })
            
            # テンポラリファイルを削除
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return extracted_text, detailed_results
        
        except Exception as e:
            raise RuntimeError(f"OCR処理エラー: {str(e)}")


# グローバルインスタンス（遅延初期化）
_ocr_service = None

def get_ocr_service():
    """OCRサービスのシングルトンインスタンスを取得"""
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
