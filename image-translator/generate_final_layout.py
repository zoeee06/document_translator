
import json, os

PARA_FILE  = "ocr_cache/paragraphs_with_id.json"
TRANS_FILE = "output/translated_with_id.json"
OUT_PATH   = "layout/page_1.json"

paragraphs = {p["id"]: p for p in json.load(open(PARA_FILE,  encoding="utf-8"))}
translations = {t["id"]: t["translated_text"] for t in json.load(open(TRANS_FILE, encoding="utf-8"))}

textRegions = []

def union_boxes(boxes):
    xs = [b[0] for b in boxes] + [b[2] for b in boxes]
    ys = [b[1] for b in boxes] + [b[3] for b in boxes]
    return [min(xs), min(ys), max(xs), max(ys)]

def cluster_lines(lines, k):
    """
    按 y 坐标自上而下扫描，动态聚类：
      1. 先按行顶 y1 升序
      2. 当前行与上一行 y‑gap < 60% 行高 → 视为同组
      3. 直到组数 == k；若多/少再做二次合并或拆分
    """
    if k <= 1 or len(lines) <= 1:
        return [lines]

    # 1) 先排序
    lines_sorted = sorted(lines, key=lambda l: l["bounding_box"][1])

    groups = [[lines_sorted[0]]]
    for cur in lines_sorted[1:]:
        prev = groups[-1][-1]
        _, py1, _, py2 = prev["bounding_box"]
        _, cy1, _, _  = cur ["bounding_box"]
        h = py2 - py1
        # 2) y 距离小于 0.6×行高 ⇒ 同组
        if abs(cy1 - py1) < 0.6 * h:
            groups[-1].append(cur)
        else:
            groups.append([cur])

    # 3) 调整组数到 k
    while len(groups) > k:                  # 组太多：把最小的一组并到上一组
        lens = [len(g) for g in groups]
        idx  = lens.index(min(lens))
        if idx == 0:
            groups[1].extend(groups[0]); groups.pop(0)
        else:
            groups[idx-1].extend(groups[idx]); groups.pop(idx)
    while len(groups) < k:                  # 组太少：把最大的一组拆成两半
        lens = [len(g) for g in groups]
        idx  = lens.index(max(lens))
        g    = groups.pop(idx)
        mid  = len(g)//2
        groups.insert(idx, g[:mid])
        groups.insert(idx+1, g[mid:])

    return groups

for pid, para in paragraphs.items():
    if pid not in translations:
        continue

    text = translations[pid].strip()
    sub_lines = text.split("\n")
    k = len(sub_lines)

    # 如果只有一行，正常输出
    if k == 1:
        x1, y1, x2, y2 = para["bounding_box"]
        textRegions.append({
            "id": pid,
            "x": x1, "y": y1,
            "width":  x2 - x1,
            "height": y2 - y1,
            "translated_text": text,
            "size": "auto", "font": "Arial-Bold",
            "color":"#ffffff", "bg_color":"#0D1033",
            "alignment":"center"
        })
        continue

    # 多行：用行级 bbox 分成 k 组
    groups = cluster_lines(para["lines"], k)

    for idx, (line_txt, group) in enumerate(zip(sub_lines, groups), 1):
    # 如果 group 为空，退而使用整段 bbox
        if not group:
            group = [ {"bounding_box": para["bounding_box"]} ]

        bx1, by1, bx2, by2 = union_boxes([l["bounding_box"] for l in group])
        textRegions.append({
        "id": f"{pid}_{idx}",
        "x": bx1, "y": by1,
        "width":  bx2 - bx1,
        "height": by2 - by1,
        "translated_text": line_txt.strip(),
        "size":"auto", "font":"Arial-Bold",
        "color":"#ffffff", "bg_color":"#0D1033",
        "alignment":"center"
    })

# 写 layout
os.makedirs("layout", exist_ok=True)
layout = {"baseImage": "input/page_1.png", "textRegions": textRegions}
json.dump(layout, open(OUT_PATH,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"✅ layout written to {OUT_PATH} ({len(textRegions)} regions)")
