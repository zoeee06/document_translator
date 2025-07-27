from google.cloud import translate_v2 as translate

# ===== 改进的翻译优化 (兼容 OpenAI 1.x) =====
def enhance_translation_with_gpt4(paragraphs, openai_client):
    """使用GPT-4直接进行高质量翻译 """
    enhanced_paragraphs = []
    
    for i, para in enumerate(paragraphs):
        text = para["text"].strip()
        
        # 跳过空文本和非中文文本
        if not text or not any('\u4e00' <= char <= '\u9fff' for char in text):
            enhanced_paragraphs.append({
                "original": text,
                "enhanced": text
            })
            continue
        
        try:
            # 使用OpenAI 1.0+ API进行翻译
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # 或 "gpt-4o" 更快更便宜
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你将翻译一些来自 PPT 或图片的中文内容。这些内容可能是完整的一句话，也可能是多个短语。\n\n"
                            "请根据以下规则进行翻译：\n"
                            "1. 如果内容中包含了标点符号，并且是完整的业务含义，请翻译为一整句英文，不要换行。\n"
                            "2. 如果内容由多个短语或术语组成（即使中间没有标点，如“品牌宣传直播带货”或“激活用户 用户关怀 提升体验”），请将每个词组翻译为简洁专业的英文术语，并用 `\n` 换行分隔。\n\n"
                            "注意事项：\n"
                            "- 不要合并内容\n"
                            "- 不要省略任何信息\n"
                            "- 所有输出必须为英文，不要包含任何中文"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"{text}"
                    }
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            enhanced_translation = response.choices[0].message.content.strip()
            
            # 确保返回的是英文翻译
            if any('\u4e00' <= char <= '\u9fff' for char in enhanced_translation):
                print(f"警告: GPT-4返回了中文文本，尝试修正...")
                # 尝试直接请求翻译
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "user", "content": f"Translate to English: {text}"}
                    ],
                    temperature=0.1
                )
                enhanced_translation = response.choices[0].message.content.strip()
            
            enhanced_paragraphs.append({
                "original": text,
                "enhanced": enhanced_translation
            })
            
            print(f"段落 {i+1} 翻译完成: {enhanced_translation[:50]}...")
        except Exception as e:
            print(f"翻译出错: {str(e)}")
            # 出错时使用Google翻译作为后备
            from google.cloud import translate_v2 as translate
            translate_client = translate.Client()
            enhanced_translation = translate_client.translate(
                text, 
                target_language="en"
            )["translatedText"]
            enhanced_paragraphs.append({
                "original": text,
                "enhanced": enhanced_translation
            })
    
    return enhanced_paragraphs