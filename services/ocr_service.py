import easyocr
import cv2
import numpy as np
from PIL import Image

class OCRService:
    """OCRリーダーサービス"""
    
    def __init__(self):
        """初期化 - 日本語と英語リーダーを準備"""
        self.reader = easyocr.Reader(['ja', 'en'], gpu=False)
    
    @staticmethod
    def imread_unicode(path):
        """日本語パス対応の画像読み込み"""
        with open(path, 'rb') as f:
            img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
            return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    
    @staticmethod
    def preprocess_image(image_path, resize_width=800):
        """画像の前処理（OCR向けに正規化）"""
        img = OCRService.imread_unicode(image_path)
        if img is None:
            raise FileNotFoundError(f"画像ファイル '{image_path}' が見つかりません")
        
        # グレースケール変換
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # コントラスト調整（CLAHE: Contrast Limited Adaptive Histogram Equalization）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # リサイズ（幅を統一してOCR精度を向上）
        h, w = enhanced.shape
        scale = resize_width / w
        new_h = int(h * scale)
        resized = cv2.resize(enhanced, (resize_width, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        return resized
    
    def extract_text(self, image_path):
        """画像からテキストを抽出"""
        try:
            # 画像の前処理
            processed_img = self.preprocess_image(image_path)
            
            # OCR実行
            results = self.reader.readtext(processed_img)
            
            # テキスト抽出
            extracted_text = '\n'.join([res[1] for res in results])
            
            # テキストと信頼度情報を返す
            detailed_results = [
                {
                    'text': res[1],
                    'confidence': res[2],
                    'bbox': res[0]
                }
                for res in results
            ]
            
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
