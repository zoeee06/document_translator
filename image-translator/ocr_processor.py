import io
from google.cloud import vision
import cv2
import numpy as np
from collections import Counter
from google.cloud import vision
from google.oauth2 import service_account   # ← 新增

CREDS = service_account.Credentials.from_service_account_file('service-key.json')

def ocr_image_with_line_info(image_path):
    print("正在执行OCR识别(带行级信息)...")
    client = vision.ImageAnnotatorClient(credentials=CREDS)

    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)
    response = client.document_text_detection(image=image)

    paragraphs = []
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:

                # -------- 段落文本 / bbox --------
                para_text = ''.join(
                    ''.join(sym.text for sym in word.symbols)
                    for word in paragraph.words
                )
                if paragraph.bounding_box.vertices:
                    v = [(pt.x, pt.y) for pt in paragraph.bounding_box.vertices]
                    xs, ys = zip(*v)
                    para_bbox = (min(xs), min(ys), max(xs), max(ys))
                else:
                    para_bbox = (0, 0, 0, 0)

                # -------- 行级信息 --------
                lines = []
                for word in paragraph.words:
                    if word.bounding_box.vertices:
                        v = [(pt.x, pt.y) for pt in word.bounding_box.vertices]
                        xs, ys = zip(*v)
                        line_bbox = (min(xs), min(ys), max(xs), max(ys))
                        line_txt = ''.join(sym.text for sym in word.symbols)
                        lines.append({"text": line_txt, "bounding_box": line_bbox})

                # --------🔹 word‑level 信息 --------
                words_info = []
                for word in paragraph.words:
                    if not word.bounding_box.vertices:
                        continue
                    poly = [(v.x, v.y) for v in word.bounding_box.vertices]
                    txt  = ''.join(sym.text for sym in word.symbols)
                    # 只要任意字符在中文 Unicode 段，就当作中文
                    is_cn = any('\u4e00' <= ch <= '\u9fff' for ch in txt)
                    words_info.append({"text": txt, "polygon": poly, "is_cn": is_cn})
                # -----------------------------------

                # 2) 再用 symbol 兜底（某些彩色字被切成单独 symbol）
                for word in paragraph.words:
                    for sym in word.symbols:
                        if not sym.bounding_box.vertices:
                            continue
                        txt = sym.text
                        if not any('\u4e00' <= ch <= '\u9fff' for ch in txt):
                            continue
                        poly = [(v.x, v.y) for v in sym.bounding_box.vertices]
                        words_info.append({"text": txt, "polygon": poly, "is_cn": True})

                paragraphs.append({
                    "id": f"r{len(paragraphs)+1}",  # 加入唯一ID
                    "text": para_text,
                    "bounding_box": para_bbox,
                    "lines": lines,
                    "words": words_info          # <‑‑ 新增
                })

    print(f"识别到 {len(paragraphs)} 个段落和 {sum(len(p['lines']) for p in paragraphs)} 行文本")
    return paragraphs


def group_text_paragraphs(paragraphs, y_threshold=30, x_threshold=350):
    """
    按 Y + X 双阈值合并相邻文本块
    - y_threshold：同一行内允许的垂直误差（像素）
    - x_threshold：当两个段落在 X 方向相隔超过此值，视为新的列段
    返回值与旧版一致
    """
    if not paragraphs:
        return []

    # 先依 y 进行粗排序
    sorted_paras = sorted(paragraphs, key=lambda p: p["bounding_box"][1])

    grouped = []
    cur = {"text":"", "bounding_box":None, "lines": []}
    last_y = sorted_paras[0]["bounding_box"][1]
    last_x = sorted_paras[0]["bounding_box"][0]

    for para in sorted_paras:
        bx, by, bx2, by2 = para["bounding_box"]
        # 条件 ①：垂直足够接近
        same_row = abs(by - last_y) < y_threshold
        # 条件 ②：水平相距不大（防止把左列 + 右列并做一段）
        same_col = abs(bx - last_x) < x_threshold

        if same_row and same_col:
            # 合并
            cur["text"] += para["text"]
            cur["lines"].extend(para["lines"])

            # 更新 bbox
            if cur["bounding_box"]:
                x1, y1, x2, y2 = cur["bounding_box"]
                cur["bounding_box"] = (
                    min(x1, bx), min(y1, by), max(x2, bx2), max(y2, by2)
                )
            else:
                cur["bounding_box"] = para["bounding_box"]
        else:
            # 先收尾
            if cur["text"]:
                grouped.append(cur)
            # 新段
            cur = {
                "text": para["text"],
                "bounding_box": para["bounding_box"],
                "lines": para["lines"]
            }

        last_y = by
        last_x = bx

    if cur["text"]:
        grouped.append(cur)

    print(f"分组后得到 {len(grouped)} 个语义段落")
    return grouped


