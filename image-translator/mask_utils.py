# mask_utils.py
import os, json
import numpy as np, cv2
from PIL import Image


def make_mask(ocr_json_path: str, img_path: str, out_mask_path: str, out_box_path: str = None):
    """根据 OCR json 里的 'words' 字段，把所有中文字 polygon 填白，并保存挖空区域位置（可选）"""
    info = json.load(open(ocr_json_path, encoding="utf-8"))
    img = Image.open(img_path)
    w, h = img.size
    mask = np.zeros((h, w), np.uint8)
    box_list = []

    for para in info:
        for wobj in para.get("words", []):
            if not any('\u4e00' <= ch <= '\u9fff' for ch in wobj["text"]):
                continue
            pts = np.array(wobj["polygon"], np.int32)
            cv2.fillPoly(mask, [pts], 255)

            x_coords = [pt[0] for pt in wobj["polygon"]]
            y_coords = [pt[1] for pt in wobj["polygon"]]
            x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
            box_list.append((x1, y1, x2, y2))

    # 轻微膨胀，防止边缘残留
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    os.makedirs(os.path.dirname(out_mask_path), exist_ok=True)
    cv2.imwrite(out_mask_path, mask)
    print("✅ mask saved →", out_mask_path)

    if out_box_path:
        # 按 y 从上到下排序
        box_list = sorted(box_list, key=lambda b: b[1])
        json.dump(box_list, open(out_box_path, "w"), indent=2)
        print("📦 mask boxes saved →", out_box_path)

make_mask(
    ocr_json_path="ocr_cache/paragraphs_with_id.json",
    img_path="input/page_1.png",
    out_mask_path="mask/page_1.png",
    out_box_path="mask/mask_boxes.json"
)

