# pngs_to_pdf.py
import glob, img2pdf, os, sys

IMG_DIR  = sys.argv[1] if len(sys.argv) > 1 else "output"  # 目录
PATTERN  = "en_page_*.png"                                 # 匹配模式
OUT_PATH = "output/final_document.pdf"

# 按文件名自然排序
images = sorted(glob.glob(os.path.join(IMG_DIR, PATTERN)))
if not images:
    raise SystemExit("❌ 没找到任何图片")

with open(OUT_PATH, "wb") as f:
    f.write(img2pdf.convert(images))
print(f"✅ 合并 {len(images)} 张 → {OUT_PATH}")
