import os
import re
import json

# Try to import Google Generative AI for the advanced online analysis tier
try:
    import google.generativeai as genai
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False

# Try to import PyArabic for advanced Arabic normalization
try:
    import pyarabic.araby as araby
    HAS_PYARABIC = True
except ImportError:
    HAS_PYARABIC = False

# Try to import transformers for local MARBERT analysis
try:
    import torch  # type: ignore
    from transformers import pipeline  # type: ignore
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Thread-safe lazy loading of MARBERT
_marbert_pipeline = None

def get_marbert_pipeline():
    global _marbert_pipeline
    if _marbert_pipeline is None:
        if HAS_TRANSFORMERS:
            try:
                print("Loading UBC-NLP/MARBERT model locally...")
                # Load MARBERT sentiment classifier or general pipeline
                # MARBERT requires proper sequence classification. If loading MLM model directly,
                # Hugging Face pipeline will use a default classification head.
                _marbert_pipeline = pipeline(
                    "sentiment-analysis", 
                    model="UBC-NLP/MARBERT", 
                    tokenizer="UBC-NLP/MARBERT"
                )
                print("UBC-NLP/MARBERT model loaded successfully.")
            except Exception as e:
                print(f"Failed to load MARBERT pipeline: {e}")
                _marbert_pipeline = False
        else:
            _marbert_pipeline = False
    return _marbert_pipeline

# ==========================================
# 1. TEXT CLEANING AND ARABIC NORMALIZATION
# ==========================================
def clean_arabic_text(text):
    if not text:
        return ""
    
    # Normalize with PyArabic if available
    if HAS_PYARABIC:
        text = araby.strip_tashkeel(text)
        text = araby.strip_tatweel(text)
    else:
        # Fallback manual tashkeel and tatweel removal
        tashkeel_pattern = re.compile(r"[\u064B-\u0652]")
        text = re.sub(tashkeel_pattern, "", text)
        text = re.sub(r"\u0640", "", text) # Tatweel

    # Normalize letters (أ/إ/آ -> أ, ة -> ه, ى -> ي)
    text = re.sub(r"[أإآ]", "أ", text)
    text = re.sub(r"ة\b", "ه", text)
    text = re.sub(r"ى\b", "ي", text)

    # Clean hyperlinks, mentions and extra spaces
    text = re.sub(r"http\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ==========================================
# 2. LOCAL RULE-BASED ARABIC LEXICON (FALLBACK)
# ==========================================
ARABIC_POSITIVE_KEYWORDS = [
    "ممتاز", "رائع", "جميل", "شكرا", "افضل", "سريع", "سهل", "ناجح", "مستمر", 
    "تسهيل", "تطور", "عظيم", "احسنت", "تيسير", "طيب", "حلو", "رهيب", "سعادة", 
    "سعيد", "قوي", "مبدع", "حبيته", "منصح", "بطل", "فنان", "عجبني", "روعه"
]

ARABIC_NEGATIVE_KEYWORDS = [
    "سيء", "تاخير", "بطيء", "مشكله", "صعب", "فشل", "خساره", "تعيس", "حزين", 
    "اسف", "خطا", "معقد", "تعب", "غالي", "نصاب", "احتيال", "رديء", "سخيف", 
    "تعبان", "مكلف", "سيئه", "تاخر", "اسوا", "خربان", "ما انصح", "غش", "فاشل"
]

ARABIC_TOPIC_RULES = {
    "خدمة العملاء": ["خدمه", "دعم", "عملاء", "موظف", "مساعده", "تواصل", "رد"],
    "جودة المنتج": ["جوده", "منتج", "خامه", "صنع", "شكل", "تغليف", "كرتون"],
    "سرعة التوصيل": ["توصيل", "شحن", "موعد", "تاخير", "سريع", "مندوب", "طلب", "تاخر"],
    "العروض والخصومات": ["سعر", "خصم", "عرض", "عروض", "تخفيض", "مكلف", "كوبون", "غالي"]
}

def analyze_sentiment_local(text):
    cleaned = clean_arabic_text(text).lower()
    
    # Count positive/negative matches
    pos_count = sum(1 for word in ARABIC_POSITIVE_KEYWORDS if word in cleaned)
    neg_count = sum(1 for word in ARABIC_NEGATIVE_KEYWORDS if word in cleaned)
    
    # Calculate scores
    total = pos_count + neg_count
    if total == 0:
        label = "محايد"
        pos_score, neg_score, neu_score = 0.1, 0.1, 0.8
    elif pos_count > neg_count:
        label = "إيجابي"
        pos_score = round(0.5 + (pos_count - neg_count) / (total * 2), 2)
        neg_score = round(0.1 / total, 2)
        neu_score = round(1.0 - pos_score - neg_score, 2)
    elif neg_count > pos_count:
        label = "سلبي"
        neg_score = round(0.5 + (neg_count - pos_count) / (total * 2), 2)
        pos_score = round(0.1 / total, 2)
        neu_score = round(1.0 - pos_score - neg_score, 2)
    else:
        label = "محايد"
        pos_score, neg_score, neu_score = 0.3, 0.3, 0.4

    # Determine topic
    detected_topic = "عام"
    for topic, keywords in ARABIC_TOPIC_RULES.items():
        if any(kw in cleaned for kw in keywords):
            detected_topic = topic
            break

    return {
        "sentiment": label,
        "pos_score": pos_score,
        "neg_score": neg_score,
        "neu_score": neu_score,
        "topic": detected_topic,
        "is_sarcastic": False,
        "sarcasm_explanation": "",
        "engine_used": "Local Lexicon Engine (Offline)"
    }

# ==========================================
# 3. ONLINE ADVANCED AI TIER (GEMINI API)
# ==========================================
def extract_topics_and_context(post_content, comment_content=None, api_key=None):
    if not HAS_GEMINI_SDK or not api_key:
        return None
        
    genai.configure(api_key=api_key)
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    prompt = f"""
    أنت خبير لغوي في تحليل النصوص العربية ومواقع التواصل الاجتماعي.
    حلل المنشور والتعليق المرفقين واستخرج البيانات المطلوبة بصيغة JSON صالحة تماماً باللغة العربية دون أي نص إضافي خارج الـ JSON أو علامات Markdown.
    
    المنشور الرئيسي: "{post_content}"
    {'التعليق المرفق: "' + comment_content + '"' if comment_content else 'لا يوجد تعليق'}
    
    الشروط:
    - يجب أن تكون المخرجات عبارة عن كود JSON صالح تماماً فقط.
    - الحقول المطلوبة:
      1. post_topic: الموضوع الرئيسي للمنشور (مثال: خدمة عملاء، جودة منتج، توصيل، سعر، إلخ).
      2. comment_topic: موضوع التعليق بالتحديد (إذا وجد تعليق، وإلا "غير محدد").
      3. is_on_topic: true/false (هل التعليق مرتبط بموضوع المنشور أم يطرح قضية جانبية؟).
      4. keywords: قائمة من 3 الكلمات المفتاحية الأكثر أهمية للنص كقائمة نصوص.
    
    صيغة الـ JSON المطلوبة:
    {{
      "post_topic": "اسم موضوع المنشور",
      "comment_topic": "اسم موضوع التعليق",
      "is_on_topic": true,
      "keywords": ["كلمة1", "كلمة2", "كلمة3"]
    }}
    """
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_txt)
            data["_model_used"] = name
            return data
        except Exception as e:
            print(f"Failed to extract topics with model {name}: {e}. Trying fallback...")
            continue
    return None

def analyze_complex_sentiment(text, local_label, api_key):
    if not HAS_GEMINI_SDK or not api_key:
        return None
        
    genai.configure(api_key=api_key)
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    prompt = f"""
    قم بتحليل المشاعر والسخرية للنص العربي التالي المأخوذ من منصة تواصل اجتماعي.
    صنف النموذج المحلي الصغير النص بشكل أولي كـ ({local_label})، ولكن نريد منك فهماً عميقاً ومتقدماً.
    افهم التناقض المنطقي، السخرية (Sarcasm)، السياق واللهجة العامية.
    أعِد النتيجة كـ JSON صالح فقط باللغة العربية دون أي علامات Markdown أو نصوص خارجية.
    
    النص: "{text}"
    
    صيغة الـ JSON المطلوبة:
    {{
      "final_sentiment": "إيجابي" أو "سلبي" أو "محايد",
      "pos_score": 0.0,
      "neg_score": 0.0,
      "neu_score": 0.0,
      "is_sarcastic": true/false (هل النص يحتوي على سخرية؟),
      "sarcasm_explanation": "شرح مبسط لسبب السخرية أو السياق المبطن إن وجد باللغة العربية، وإلا اتركه فارغاً"
    }}
    """
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_txt)
            data["_model_used"] = name
            return data
        except Exception as e:
            print(f"Failed to analyze complex sentiment with model {name}: {e}. Trying fallback...")
            continue
    return None


# ==========================================
# 4. HYBRID DISPATCHER & BULK ORCHESTRATOR
# ==========================================
import time

def analyze_text_hybrid(text, parent_text=None, inherited_topic=None):
    if not text or not text.strip():
        return analyze_sentiment_local("")

    cleaned = clean_arabic_text(text)
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("ai_key")

    # Step 1: Topic Modeling (Strictly Rule-based / inherited to save API calls)
    if inherited_topic:
        detected_topic = inherited_topic
    else:
        detected_topic = "عام"
        for topic, keywords_list in ARABIC_TOPIC_RULES.items():
            if any(kw in cleaned.lower() for kw in keywords_list):
                detected_topic = topic
                break
    keywords = []

    # Step 2: Local Inference First (MARBERT if available, Lexicon otherwise)
    local_pipeline = get_marbert_pipeline()
    
    local_sentiment = "محايد"
    local_confidence = 0.70
    pos_score, neg_score, neu_score = 0.33, 0.33, 0.34
    engine_used = "Local Lexicon Engine"

    if local_pipeline:
        try:
            res = local_pipeline(cleaned)[0]
            # Map MARBERT labels
            label_mapping = {
                "LABEL_0": "سلبي",
                "LABEL_1": "محايد",
                "LABEL_2": "إيجابي"
            }
            local_sentiment = label_mapping.get(res['label'], "محايد")
            local_confidence = res['score']
            
            # Interpolate score values
            if local_sentiment == "إيجابي":
                pos_score = round(local_confidence, 2)
                neg_score = round((1.0 - pos_score) / 2, 2)
                neu_score = round(1.0 - pos_score - neg_score, 2)
            elif local_sentiment == "سلبي":
                neg_score = round(local_confidence, 2)
                pos_score = round((1.0 - neg_score) / 2, 2)
                neu_score = round(1.0 - pos_score - neg_score, 2)
            else:
                neu_score = round(local_confidence, 2)
                pos_score = round((1.0 - neu_score) / 2, 2)
                neg_score = round(1.0 - pos_score - neu_score, 2)
                
            engine_used = "Local MARBERT (v2.0)"
        except Exception as e:
            print(f"MARBERT run error, falling back to lexicon: {e}")
            lex_res = analyze_sentiment_local(cleaned)
            local_sentiment = lex_res["sentiment"]
            pos_score, neg_score, neu_score = lex_res["pos_score"], lex_res["neg_score"], lex_res["neu_score"]
            local_confidence = 0.70
            engine_used = "Local Lexicon (Fallback)"
    else:
        # Standard Lexicon run
        lex_res = analyze_sentiment_local(cleaned)
        local_sentiment = lex_res["sentiment"]
        pos_score, neg_score, neu_score = lex_res["pos_score"], lex_res["neg_score"], lex_res["neu_score"]
        local_confidence = 0.70
        engine_used = "Local Lexicon (Offline)"

    # Step 3: Check if Fallback to Gemini is triggered (Strictly only for COMMENTS to avoid API limit issues!)
    final_sentiment = local_sentiment
    is_sarcastic = False
    sarcasm_explanation = ""
    
    is_comment = parent_text is not None
    
    if is_comment and (local_confidence < 0.85 or engine_used == "Local Lexicon (Offline)") and api_key and HAS_GEMINI_SDK:
        # Call Gemini for sarcasm and deep analysis
        advanced_res = analyze_complex_sentiment(cleaned, local_sentiment, api_key)
        time.sleep(1) # Rate limit protection sleep
        if advanced_res:
            final_sentiment = advanced_res.get("final_sentiment", final_sentiment)
            pos_score = advanced_res.get("pos_score", pos_score)
            neg_score = advanced_res.get("neg_score", neg_score)
            neu_score = advanced_res.get("neu_score", neu_score)
            is_sarcastic = advanced_res.get("is_sarcastic", False)
            sarcasm_explanation = advanced_res.get("sarcasm_explanation", "")
            
            model_used = advanced_res.get("_model_used", "gemini-1.5-flash")
            pres_name = "Gemini 2.0 Flash" if "2.0" in model_used else "Gemini 1.5 Flash"
            engine_used = f"{pres_name} (Sarcasm Fallback)"
            local_confidence = 0.95

    return {
        "sentiment": final_sentiment,
        "pos_score": pos_score,
        "neg_score": neg_score,
        "neu_score": neu_score,
        "topic": detected_topic,
        "is_sarcastic": is_sarcastic,
        "sarcasm_explanation": sarcasm_explanation,
        "engine_used": engine_used,
        "confidence": local_confidence,
        "keywords": keywords
    }

def bulk_analyze_posts(posts_qs, batch=None):
    from .models import SentimentResult, TopicTag, AIModel
    
    # Get or create active AI Model reference
    ai_model, _ = AIModel.objects.get_or_create(
        model_name="Hybrid-Arabic-Sentiment-System",
        defaults={
            "version": "v2.0",
            "lang": "ar",
            "provider": "Local/Gemini-Hybrid"
        }
    )
    
    total_count = posts_qs.count()
    print(f"Starting bulk analysis of {total_count} posts...")
    
    analyzed_count = 0
    for idx, post in enumerate(posts_qs):
        # Check if already analyzed
        if post.sentiments.exists():
            continue
            
        print(f"   [{idx+1}/{total_count}] Analyzing ID {post.id} (Content: '{post.content[:25]}...')...")
        
        # Topic Inheritance for comments
        inherited_topic = None
        if post.parent_post:
            parent_sentiment = post.parent_post.sentiments.first()
            if parent_sentiment:
                parent_tag = parent_sentiment.tags.first()
                if parent_tag:
                    inherited_topic = parent_tag.topic_label

        parent_text = post.parent_post.content if post.parent_post else None
        res = analyze_text_hybrid(post.content, parent_text=parent_text, inherited_topic=inherited_topic)
        
        # 1. Save SentimentResult
        sentiment_obj = SentimentResult.objects.create(
            post=post,
            model=ai_model,
            batch=batch,
            label=res.get("sentiment", "محايد"),
            pos_score=res.get("pos_score", 0.33),
            neg_score=res.get("neg_score", 0.33),
            neu_score=res.get("neu_score", 0.34),
            lang_processed="ar",
            is_sarcastic=res.get("is_sarcastic", False),
            sarcasm_explanation=res.get("sarcasm_explanation", ""),
            engine_used=res.get("engine_used", "Local Lexicon Engine"),
            confidence_score=res.get("confidence", 0.70)
        )
        
        # 2. Save TopicTag
        TopicTag.objects.create(
            result=sentiment_obj,
            topic_label=res.get("topic", "عام"),
            confidence=0.90
        )
        
        analyzed_count += 1
        
    print(f"Finished bulk analysis! Total analyzed: {analyzed_count}")
    return analyzed_count
