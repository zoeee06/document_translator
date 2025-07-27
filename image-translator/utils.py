# utils.py
import cv2
import numpy as np
from PIL import Image
from collections import Counter

import os
import json
import xml.etree.ElementTree as ET


# utils.py
def generate_enhanced_mapping_with_lines(paragraphs, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("专业优化版段落翻译（含行级位置信息）\n")
        f.write("=" * 80 + "\n\n")
        
        for i, para in enumerate(paragraphs):
            f.write(f"段落 {i+1}:\n")
            f.write(f"原文: {para.get('original', '')}\n")
            f.write(f"优化翻译: {para.get('enhanced', '')}\n")
            
            # 修改标签为"位置:"（去掉"段落"前缀）
            if 'bounding_box' in para:
                x1, y1, x2, y2 = para['bounding_box']
                f.write(f"位置: {x1},{y1},{x2},{y2}\n")  # 修改这里
            
            # 保存行级位置信息
            if 'lines' in para:
                f.write("行位置:\n")  # 修改标签
                for j, line in enumerate(para['lines']):
                    # 确保行级数据有边界框
                    if 'bounding_box' in line:
                        x1, y1, x2, y2 = line['bounding_box']
                        # 格式：行ID|翻译文本|坐标
                        translated_text = line.get('translated_text', '')
                        f.write(f"行{j+1}: {translated_text}|{x1},{y1},{x2},{y2}\n")
            
            f.write("-" * 80 + "\n\n")

# utils.py
def merge_overlapping(regions, iou_thresh=0.6):
    """
    简单两两遍历，IOU > iou_thresh 就合并
    返回新的 regions 列表
    """
    merged = []
    for reg in regions:
        bx1, by1, bw, bh = reg["x"], reg["y"], reg["width"], reg["height"]
        bx2, by2 = bx1 + bw, by1 + bh
        placed = False
        for m in merged:
            mx1, my1, mw, mh = m["x"], m["y"], m["width"], m["height"]
            mx2, my2 = mx1 + mw, my1 + mh
            # 计算 IOU
            ix1, iy1 = max(bx1, mx1), max(by1, my1)
            ix2, iy2 = min(bx2, mx2), min(by2, my2)
            inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
            union = bw*bh + mw*mh - inter
            iou = inter / union if union else 0
            if iou > iou_thresh:
                # union box
                nx1, ny1 = min(bx1, mx1), min(by1, my1)
                nx2, ny2 = max(bx2, mx2), max(by2, my2)
                m["x"], m["y"] = nx1, ny1
                m["width"], m["height"] = nx2 - nx1, ny2 - ny1
                # 拼接文本（换行）
                m["translated_text"] += "\n" + reg["translated_text"]
                placed = True
                break
        if not placed:
            merged.append(reg)
    return merged
