import os
import re

def rebuild():
    bak_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py.bak"
    file_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py"
    
    if not os.path.exists(bak_path):
        print("Backup file not found!")
        return
        
    # Read original raw backup
    with open(bak_path, 'rb') as f:
        raw_bytes = f.read()
        
    # Decode as UTF-8 replacing any corrupted byte
    text = raw_bytes.decode('utf-8', errors='replace')
    print("Read original file content successfully.")
    
    # 1. Add 'import time' at the top
    if "import time" not in text:
        text = text.replace("import json", "import json\nimport time")
        print("Added 'import time' to imports.")
        
    # 2. Re-write/Replace get_ai_topic_modeling and extract_topics_and_context
    corrupted_part_pattern = re.compile(
        r"def extract_topics_and_context\(.*?return \{\"topic\": \"عام\", \"keywords\": \[\]\}",
        re.DOTALL
    )
    
    new_fns_content = """def get_ai_topic_modeling(text, api_key=None):
    if not HAS_GEMINI_SDK or not api_key or not text or not text.strip():
        return {"topic": "عام", "keywords": []}
        
    genai.configure(api_key=api_key)
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    prompt = f\"\"\"
    قم بتحليل النص التالي واستخرج الموضوع الأساسي والكلمات المفتاحية ككود JSON صالح فقط باللغة العربية دون أي نصوص إضافية أو علامات Markdown:
    
    النص: "{text}"
    
    المطلوب:
    1. topic: الموضوع الأساسي للنص بكلمة أو اثنتين فقط (مثال: خدمة عملاء، جودة منتج، سرعة توصيل، أسعار وعروض، إلخ).
    2. keywords: قائمة تحتوي على أهم 3 كلمات مفتاحية في النص.
    
    صيغة الـ JSON المطلوبة:
    {{
      "topic": "اسم الموضوع",
      "keywords": ["كلمة1", "كلمة2", "كلمة3"]
    }}
    \"\"\"
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_txt)
            return {
                "topic": data.get("topic", "عام"),
                "keywords": data.get("keywords", [])
            }
        except Exception as e:
            print(f"Failed to extract topic with {name}: {e}")
            continue
            
    return {"topic": "عام", "keywords": []}


def analyze_complex_sentiment(text, local_sentiment, api_key):
    if not HAS_GEMINI_SDK or not api_key or not text or not text.strip():
        return None
        
    genai.configure(api_key=api_key)
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    prompt = f\"\"\"
    أنت خبير لغوي متخصص في تحليل المشاعر والآراء على منصات التواصل الاجتماعي، ومحترف في كشف السخرية والتهكم المبطن (Sarcasm) في اللهجات العربية المختلفة (خاصة الشامية والمصرية والخليجية).
    
    قم بتحليل النص التالي بدقة مع الأخذ في الاعتبار أن التصنيف المحلي المبدئي للمشاعر هو: "{local_sentiment}".
    
    النص المراد تحليله: "{text}"
    
    المطلوب استخراجه:
    1. final_sentiment: تحديد المشاعر النهائية بدقة (إيجابي، سلبي، أو محايد). انتبه جداً للسخرية؛ النص الساخر الذي يظهر كإيجابي هو في الحقيقة سلبي جداً!
    2. pos_score: درجة الإيجابية كقيمة عشرية بين 0.0 و 1.0.
    3. neg_score: درجة السلبية كقيمة عشرية بين 0.0 و 1.0.
    4. neu_score: درجة الحياد كقيمة عشرية بين 0.0 و 1.0.
    (ملاحظة: مجموع الدرجات الثلاث يجب أن يكون قريباً جداً من 1.0).
    5. is_sarcastic: قيمة منطقية (true إذا كان النص يحتوي على سخرية أو تهكم مبطن، وإلا false).
    6. sarcasm_explanation: شرح مبسط ومختصر جداً باللغة العربية لسبب اعتبار النص ساخراً (إذا كان كذلك)، وإلا اتركه فارغاً "".
    7. topic: تصنيف موضوع النص بكلمة أو اثنتين فقط (مثال: خدمة عملاء، جودة منتج، سرعة توصيل، أسعار وعروض، إلخ).
    8. keywords: قائمة تحتوي على أهم 3 كلمات مفتاحية في النص.
    
    يجب أن تكون المخرجات عبارة عن كود JSON صالح تماماً فقط باللغة العربية، دون أي نصوص إضافية أو علامات Markdown أو ```json.
    
    صيغة الـ JSON المطلوبة:
    {{
      "final_sentiment": "إيجابي/سلبي/محايد",
      "pos_score": 0.1,
      "neg_score": 0.8,
      "neu_score": 0.1,
      "is_sarcastic": true,
      "sarcasm_explanation": "شرح السخرية هنا",
      "topic": "موضوع النص",
      "keywords": ["كلمة1", "كلمة2", "كلمة3"]
    }}
    \"\"\"
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_txt)
            
            final_sent = data.get("final_sentiment", local_sentiment)
            if final_sent not in ["إيجابي", "سلبي", "محايد"]:
                final_sent = local_sentiment
                
            return {
                "final_sentiment": final_sent,
                "pos_score": float(data.get("pos_score", 0.33)),
                "neg_score": float(data.get("neg_score", 0.33)),
                "neu_score": float(data.get("neu_score", 0.34)),
                "is_sarcastic": bool(data.get("is_sarcastic", False)),
                "sarcasm_explanation": data.get("sarcasm_explanation", ""),
                "topic": data.get("topic", "عام"),
                "keywords": data.get("keywords", []),
                "_model_used": name
            }
        except Exception as e:
            print(f"Failed complex sentiment analysis with {name}: {e}")
            continue
            
    return None"""
    
    text, count = corrupted_part_pattern.subn(new_fns_content, text)
    print(f"Replaced corrupted AI/Topic block: {count} matches replaced.")
    
    # 3. Remove the FIRST (corrupted) duplicate bulk_analyze_posts function
    dup_pattern = re.compile(
        r"def bulk_analyze_posts\(posts_qs, batch=None\):.*?\"keywords\": keywords\s*\}",
        re.DOTALL
    )
    
    text, count_dup = dup_pattern.subn("", text, count=1)
    print(f"Removed duplicated bulk_analyze_posts function: {count_dup} matches removed.")
    
    # 4. Fix Arabic has_custom_match logic to check ONLY external user lexicons (ext_pos/ext_neg)
    # instead of falsely matching the built-in massive list
    old_match_block = """        # Load dynamic lexicon keywords to check if the user's custom dictionary was matched
        ext_pos = load_external_keywords(POS_FILE)
        ext_neg = load_external_keywords(NEG_FILE)
        all_pos = list(set(ARABIC_POSITIVE_KEYWORDS + ext_pos))
        all_neg = list(set(ARABIC_NEGATIVE_KEYWORDS + ext_neg))
        
        lex_pos_count = sum(1 for word in all_pos if word in cleaned.lower())
        lex_neg_count = sum(1 for word in all_neg if word in cleaned.lower())
        has_custom_match = (lex_pos_count + lex_neg_count) > 0

        if has_custom_match:
            local_confidence = 0.95
            if "MARBERT" in engine_used:
                engine_used = "Local MARBERT (Keyword Match)"
            else:
                engine_used = "Local Lexicon (Keyword Match)\""""
                
    # Use re.escape or a simple replacement for the exact text block
    target_block = """        # Load dynamic lexicon keywords to check if the user's custom dictionary was matched
        ext_pos = load_external_keywords(POS_FILE)
        ext_neg = load_external_keywords(NEG_FILE)
        all_pos = list(set(ARABIC_POSITIVE_KEYWORDS + ext_pos))
        all_neg = list(set(ARABIC_NEGATIVE_KEYWORDS + ext_neg))
        
        lex_pos_count = sum(1 for word in all_pos if word in cleaned.lower())
        lex_neg_count = sum(1 for word in all_neg if word in cleaned.lower())
        has_custom_match = (lex_pos_count + lex_neg_count) > 0

        if has_custom_match:
            local_confidence = 0.95
            if "MARBERT" in engine_used:
                engine_used = "Local MARBERT (Keyword Match)"
            else:
                engine_used = "Local Lexicon (Keyword Match)\""""
                
    replacement_block = """        # Load dynamic lexicon keywords to check if the user's custom dictionary was matched
        ext_pos = load_external_keywords(POS_FILE)
        ext_neg = load_external_keywords(NEG_FILE)
        
        custom_pos_count = sum(1 for word in ext_pos if word in cleaned.lower())
        custom_neg_count = sum(1 for word in ext_neg if word in cleaned.lower())
        has_custom_match = (custom_pos_count + custom_neg_count) > 0

        if has_custom_match:
            local_confidence = 0.95
            if "MARBERT" in engine_used:
                engine_used = "Local MARBERT (Custom Match)"
            else:
                engine_used = "Local Lexicon (Custom Match)\""""
                
    if target_block in text:
        text = text.replace(target_block, replacement_block)
        print("Successfully fixed has_custom_match logic block in rebuilder!")
    else:
        # Fallback to a looser replace just in case of slight space variances
        print("Warning: exact custom match block not found, trying normalized replace...")
        text = text.replace("lex_pos_count = sum(1 for word in all_pos if word in cleaned.lower())", "custom_pos_count = sum(1 for word in ext_pos if word in cleaned.lower())")
        text = text.replace("lex_neg_count = sum(1 for word in all_neg if word in cleaned.lower())", "custom_neg_count = sum(1 for word in ext_neg if word in cleaned.lower())")
        text = text.replace("has_custom_match = (lex_pos_count + lex_neg_count) > 0", "has_custom_match = (custom_pos_count + custom_neg_count) > 0")
        text = text.replace('engine_used = "Local MARBERT (Keyword Match)"', 'engine_used = "Local MARBERT (Custom Match)"')
        text = text.replace('engine_used = "Local Lexicon (Keyword Match)"', 'engine_used = "Local Lexicon (Custom Match)"')
        print("Applied fallback replacements for has_custom_match logic.")
        
    # Write back clean file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Successfully built clean sentiment_engine.py!")

if __name__ == '__main__':
    rebuild()
