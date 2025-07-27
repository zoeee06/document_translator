import json, os
from ocr_processor import ocr_image_with_line_info

IMG = "input/page_1.png"                 # ← 图片路径
SAVE_AS = "ocr_cache/paragraphs_with_id.json"        # ← 输出文件

data = ocr_image_with_line_info(IMG)
os.makedirs(os.path.dirname(SAVE_AS), exist_ok=True)
with open(SAVE_AS, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ OCR 结果已保存 →", SAVE_AS)