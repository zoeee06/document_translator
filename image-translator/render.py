
import cv2                          # 新增
import numpy as np                  # 如果 draw_text_fit 里已经 import 就跳过
import json, os, glob
from PIL import Image, ImageDraw, ImageFont
import textwrap
from style import BG_COLOR, DEFAULT_COLOR, DEFAULT_FONT, MIN_FONT_PX
import os

# ---------- util ----------
def hex_to_rgb(hexstr):
    """'#RRGGBB' -> (r,g,b)"""
    hexstr = hexstr.lstrip("#")
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))


def draw_text_fit(draw, bbox, text, font_path, init_px, fill=DEFAULT_COLOR, align="center"):
    """
    自动缩放字体 + 支持人工换行 \\n + 自动换行时避免断词 + 居中绘制
    """
    x1, y1, x2, y2 = bbox
    max_w, max_h = x2 - x1, y2 - y1
    size = init_px
    font, lines, line_h, total_h = None, [], 0, 0

    while size >= MIN_FONT_PX:
        font = ImageFont.truetype(font_path, size)
        line_h = font.getbbox("Hy")[3]  # 行高

        if "\n" in text:
            # 人工换行，优先保留
            lines = text.split("\n")
        else:
            # 优先尝试单行
            if draw.textlength(text, font=font) <= max_w:
                lines = [text]
            else:
                # 自动换行，避免在单词中间断开
                avg_char_w = font.getlength("A") or 1
                wrap_w = max(int(max_w / avg_char_w), 1)
                lines = textwrap.wrap(
                    text,
                    width=wrap_w,
                    break_long_words=False,
                    break_on_hyphens=False
                )

        total_h = line_h * len(lines)
        max_line_w = max(draw.textlength(line, font=font) for line in lines)

        if total_h <= max_h and max_line_w <= max_w:
            break
        size -= 1

    # 居中绘制文本
    cur_y = y1 + (max_h - total_h) / 2
    for line in lines:
        line_w = draw.textlength(line, font=font)
        if align == "left":
            cur_x = x1                       # 靠左
        elif align == "right":
            cur_x = x2 - line_w              # 靠右
        else:                                # center
            cur_x = x1 + (max_w - line_w) / 2
        draw.text((cur_x, cur_y), line, fill=fill, font=font)
        cur_y += line_h

    return font.size




# ---------- main render ----------
def render_one(layout_json, output_dir="output"):
    with open(layout_json, encoding="utf-8") as f:
        cfg = json.load(f)

    base_img_path = cfg["baseImage"]
    img = Image.open(base_img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    for reg in cfg["textRegions"]:
        x, y, w, h = reg["x"], reg["y"], reg["width"], reg["height"]
        bbox = (x, y, x + w, y + h)

        # 1) 填背景 -----------------------------
        bg = reg.get("bg_color", "$BG")

        # --- Mode C: pixel‑level mask / inpaint ---
        if bg == "$MASK":
            base_name = os.path.splitext(os.path.basename(cfg["baseImage"]))[0]
            mask_path = f"mask/{base_name}.png"
            if not os.path.exists(mask_path):
                print("⚠️ 找不到掩膜，跳过 mask 处理")
            else:
                mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
                img_np = np.array(img)

                x1, y1, x2, y2 = bbox
                roi = img_np[y1:y2, x1:x2]
                if roi.std() < 10:                     # 纯色
                    dom = np.mean(roi.reshape(-1, 3), axis=0)
                    img_np[mask > 0] = dom
                else:                                  # 渐变/图案
                    img_np = cv2.inpaint(img_np, mask, 3, cv2.INPAINT_NS)

                img = Image.fromarray(img_np)
                draw = ImageDraw.Draw(img)

        # --- Mode A/B: 纯色覆盖 -----------------
        elif bg != "$NONE":
            fill = hex_to_rgb(BG_COLOR if bg == "$BG" else bg)
            draw.rectangle(bbox, fill=fill)
        # （bg == "$NONE" 时直接跳过覆盖）

        # 2) 写英文 ------------------------------
        txt = reg["translated_text"]
        if txt.strip():                                # 避免空字符串报错
            font_name = reg.get("font", DEFAULT_FONT)
            if font_name.lower().endswith(".ttf"):      # 已经是文件名
                font_path = os.path.join("fonts", font_name)
            else:                                       # 只是逻辑名，自己补 .ttf
                font_path = f"fonts/{font_name}.ttf"



            _, y1, _, y2 = reg["y"], reg["y"], reg["y"] + reg["height"], reg["y"] + reg["height"]
            box_height = y2 - y1
            if str(reg.get("size", "")).lower().endswith("px"):
                init_px = int(reg["size"].rstrip("px"))
            else:
                box_height = reg["height"]
                init_px = int(box_height * 0.75)
            color = reg.get("color", DEFAULT_COLOR)
            align = reg.get("alignment", "center").lower()
            final_px = draw_text_fit(draw, bbox, txt, font_path, init_px, fill=color, align=align)
            reg["size"] = f"{final_px}px"


    # 保存
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "en_" + os.path.basename(base_img_path))
    img.save(out_path)
    print(f"✅ 渲染完成 → {out_path}")
    # --- 在 render_one 最后、保存输出图片之后 ---
    filled_dir = "layout_filled"
    os.makedirs(filled_dir, exist_ok=True)

    # ② 文件名与原 layout 对应
    filled_json = os.path.join(
        filled_dir,
        os.path.basename(layout_json).replace(".json", "_filled.json")
    )

    # ③ 写文件
    with open(filled_json, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    print(f"📄 实际字号已写回 → {filled_json}")


# ---------- CLI ----------
if __name__ == "__main__":
    os.makedirs("output", exist_ok=True)
    for layout in glob.glob("layout/*.json"):
        render_one(layout)


