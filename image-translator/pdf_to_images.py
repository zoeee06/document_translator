# pdf_to_images.py
"""
把纯图片 PDF 拆页转成 png，存到 input/ 目录
用 pdf2image + Poppler，自动按 page_1.png、page_2.png 命名
"""

import os, sys
from pdf2image import convert_from_path

PDF_PATH = sys.argv[1] if len(sys.argv) > 1 else "source.pdf"
OUT_DIR  = "input"
DPI      = 300                # 建议 300；太低影响 OCR

def pdf_to_pngs(pdf_path, out_dir, dpi=DPI):
    os.makedirs(out_dir, exist_ok=True)
    pages = convert_from_path(pdf_path, dpi=dpi)
    for i, page in enumerate(pages, 1):
        fname = f"page_{i}.png"
        fpath = os.path.join(out_dir, fname)
        page.save(fpath)
        print(f"🖼  {fpath}")
    return len(pages)

if __name__ == "__main__":
    n = pdf_to_pngs(PDF_PATH, OUT_DIR)
    print(f"✅ {PDF_PATH} → {n} PNGs in {OUT_DIR}/")
