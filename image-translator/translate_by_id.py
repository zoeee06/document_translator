import json
from translation import enhance_translation_with_gpt4
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    raise ValueError("❌ OPENAI_API_KEY not found. Please set it in .env file.")

# 设置路径
INPUT_JSON = "ocr_cache/paragraphs_with_id.json"
OUTPUT_JSON = "translated_with_id.json"
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Step 1：读取带 ID 的段落
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    paragraphs = json.load(f)

# Step 2：翻译（保持原顺序）
translated_result = enhance_translation_with_gpt4(paragraphs, openai_client)

# Step 3：组装为带 ID 的结构
final_output = []
for orig, trans in zip(paragraphs, translated_result):
    final_output.append({
        "id": orig["id"],
        "translated_text": trans["enhanced"]
    })

# Step 4：保存
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(final_output, f, ensure_ascii=False, indent=2)

print("✅ 翻译完成，输出 saved to translated_with_id.json")
