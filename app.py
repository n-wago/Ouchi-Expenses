import easyocr
import cv2
import numpy as np

# 1. OCRリーダーの初期化（日本語と英語を指定）
reader = easyocr.Reader(['ja', 'en'])

# 日本語パス対応の画像読み込み関数
def imread_unicode(path):
    with open(path, 'rb') as f:
        img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)

# 2. 画像ファイルのパスを指定
image_path = 'receipt.jpg'
img = imread_unicode(image_path)

# 3. 文字読み取りの実行
if img is None:
    print(f"エラー：画像ファイル '{image_path}' が見つかりません。")
else:
    print("読み込み中…")
    results = reader.readtext(img)

    # 4. 結果の表示
    print("-" * 30)
    print("【読み取り結果】")
    for res in results:
        print(res[1])
    print("-" * 30)