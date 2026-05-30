import os

import re

import json
import time



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



# Try to import NLTK and VADER for advanced offline English analysis

try:

    import nltk

    from nltk.sentiment.vader import SentimentIntensityAnalyzer

    HAS_NLTK_VADER = True

    # Pre-download VADER lexicon at runtime automatically if not present

    try:

        nltk.data.find('sentiment/vader_lexicon.zip')

    except LookupError:

        try:

            nltk.download('vader_lexicon', quiet=True)

        except Exception:

            pass

except ImportError:

    HAS_NLTK_VADER = False



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

    # الكلمات الأصلية

    "ممتاز", "رائع", "جميل", "شكرا", "افضل", "سريع", "سهل", "ناجح", "مستمر", 

    "تسهيل", "تطور", "عظيم", "احسنت", "تيسير", "طيب", "حلو", "رهيب", "سعادة", 

    "سعيد", "قوي", "مبدع", "حبيته", "منصح", "بطل", "فنان", "عجبني", "روعه",

    # 100 كلمة جديدة

    "أسطوري", "خيالي", "مذهل", "متألق", "ابداع", "احترافي", "خرافي", "تحفة", 

    "يشكرون", "كفو", "يعطيكم العافية", "راقي", "فخم", "يجنن", "يهبل", "مضبوط", 

    "مضمون", "ثقة", "اصلي", "يستحق", "جبار", "دقيق", "متفوق", "مريح", "مرتب", 

    "نظيف", "محترم", "راحة", "امان", "خفيف", "لذيذ", "ممتع", "مفيد", "عملي", 

    "متين", "توفير", "خبير", "عبقري", "مبتكر", "ذكي", "متكامل", "شامل", "ملهم", 

    "مشوق", "جذاب", "انيق", "سحر", "يفوز", "يستاهل", "بيرفكت", "توب", "خلوق", 

    "نمبر وان", "رهابة", "ابهار", "متعاون", "بشوش", "لطيف", "ذوق", "كلاس", 

    "صفقة", "رابح", "فوز", "انتصار", "مبهر", "مدهش", "امين", "صادق", "وفي", 

    "مخلص", "انجاز", "فخر", "اعتزاز", "ينقذ", "منقذ", "تحسين", "ترقية", "تحديث", 

    "مرن", "سلس", "متوافق", "ممتازين", "بديع", "خالص", "متقن", "ناصع", "باهر", 

    "فريد", "استثنائي", "نموذجي", "أصيل", "آمن", "فعال", "حصري", "إيجابي", 

    "رايع", "يبيض الوجه", "ابداعي", "منظم", "يشكر"

]



ARABIC_NEGATIVE_KEYWORDS = [

    # الكلمات الأصلية

    "سيء", "تاخير", "بطيء", "مشكله", "صعب", "فشل", "خساره", "تعيس", "حزين", 

    "اسف", "خطا", "معقد", "تعب", "غالي", "نصاب", "احتيال", "رديء", "سخيف", 

    "تعبان", "مكلف", "سيئه", "تاخر", "اسوا", "خربان", "ما انصح", "غش", "فاشل",

    # 100 كلمة جديدة

    "زبالة", "قرف", "نصب", "كذب", "حرامية", "غشاش", "فاشلين", "مقلب", "ندمت", 

    "تحذير", "ابتعدوا", "مهزلة", "كارثة", "مصيبة", "دمار", "خيبة", "مقرف", "بشع", 

    "قبيح", "تالف", "مكسور", "ناقص", "مستعمل", "قديم", "مصدي", "معفن", "يفشل", 

    "زفت", "طين", "خياس", "مبالغ", "استغلال", "طمع", "جشع", "مماطلة", "تطنيش", 

    "تجاهل", "وقح", "مستفز", "يقهر", "يعل", "غثيث", "علة", "هم", "ضياع", "فوضى", 

    "عشوائية", "وسخ", "قذر", "ريحة", "مزعج", "ضجيج", "ميت", "معلق", "خرب", 

    "يخرب", "عطلان", "متعطل", "وهمي", "مزيف", "تقليد", "مضروب", "بلوك", "شكوى", 

    "استرجاع", "سرقة", "مسروق", "غبي", "جاهل", "مبتدئ", "استهتار", "تقصير", 

    "عيب", "عيوب", "تلف", "تسريب", "بهذلة", "مرمطة", "عذاب", "ردي", "رديئ", 

    "شنيع", "مريع", "كارثي", "مخيب", "بائس", "مؤسف", "مقزز", "ممل", "مزري", 

    "ضعيف", "هش", "ردائة", "مشبوه", "خادع", "مزور", "مخادع", "سيئين", "منحط"

]

# Conservative sarcasm detection — hyperbolic praise and ironic markers only
SARCASM_HYPERBOLIC_PRAISE = {
    'ممتاز', 'رائع', 'خيال', 'خيالي', 'اسطور', 'اسطوري', 'أسطوري', 'تحف', 'تحفة',
    'genius', 'perfect', 'بيرفكت', 'خراف', 'خرافي', 'مذهل', 'رهيب', 'عظيم', 'fabulous',
    'اسطور', 'يجنن', 'يهبل', 'مبدع', 'عبقري', 'تحفة', 'اسطوري',
}
SARCASM_DEGREE_TRIGGERS = ('لدرجة ان', 'لدرجة إن', 'لدرجة', 'لدرجه')
SARCASM_IRONIC_EMOJIS = ('🔥', '👏', '😂', '😅')
MIN_STEM_MATCH_LEN = 4

POSITIVE_BLESSING_PHRASES = (
    'الله يفتح', 'يفتحها عليكم', 'يفتحها عليك', 'بارك الله', 'ما شاء الله', 'ماشاء الله',
    'اية الرزق', 'آية الرزق', 'الله يبارك', 'ربنا يبارك', 'جعله الله', 'في ميزان حسنات',
    'الله يعطيكم العافية', 'الله يعطيك العافية', 'كل عام وانتم بخير', 'كل عام وأنتم بخير',
)

NEUTRAL_INFO_PATTERNS = (
    r'كم\s+سعر', r'كم\s+السعر', r'كم\s+بيكلف', r'كم\s+بيعمل',
    r'وكم\s+سعر', r'بكم\s+', r'سعرها\b', r'سعره\b',
    r'كيف\s+الاسعار', r'كيف\s+الأسعار', r'شو\s+الاسعار', r'شو\s+الأسعار',
    r'ممكن\s+نعرف', r'بدي\s+اعرف\s+السعر', r'بدي\s+أعرف\s+السعر',
    r'موجود\s+.+\s+سعر', r'عندكم\s+.+\s+سعر',
)
SARCASM_SURFACE_PRAISE = {'شغال', 'شغالة', 'ممتاز', 'رائع', 'سريع', 'سريعة', 'perfect', 'بيرفكت'}
SARCASM_NEGATIVE_METAPHORS = {
    'دفاية', 'دفايه', 'دفّاية', 'حر', 'حار', 'سخن', 'سخنة',
    'ما بفتح', 'ما بتفتح', 'ما يفتح', 'ما بيفتح', 'ما بشتغل', 'ما يشتغل',
}


def _text_has_hyperbolic_praise(text):
    cleaned = clean_arabic_text(text).lower() if text else ""
    return any(word in cleaned for word in SARCASM_HYPERBOLIC_PRAISE)


def _text_has_any_positive_sentiment(text):
    if not text:
        return False
    cleaned = clean_arabic_text(text).lower()
    if _text_has_hyperbolic_praise(text):
        return True
    return any(kw in cleaned for kw in ARABIC_POSITIVE_KEYWORDS)


def _is_menu_price_listing(text):
    cleaned = clean_arabic_text(text).lower() if text else ""
    has_price = bool(re.search(r'\d+\s*(دينار|jd|د\.?\s*ع)', cleaned)) or 'دينار' in cleaned
    has_product = any(w in cleaned for w in ('سدر', 'منسف', 'كيلو', 'طبق', 'وجبة', 'مطبخ', 'لحم'))
    has_complaint = any(w in cleaned for w in ('غالي', 'نصب', 'استغلال', 'سيء', 'ردي', 'زفت', 'مبالغ'))
    return has_price and has_product and not has_complaint


def _classify_text_context(text):
    """Detect clear non-sarcastic contexts: blessings, price inquiries, menu listings."""
    if not text or not text.strip():
        return None
    cleaned = clean_arabic_text(text).lower()

    if any(phrase in cleaned for phrase in POSITIVE_BLESSING_PHRASES):
        return "positive_blessing"

    for pattern in NEUTRAL_INFO_PATTERNS:
        if re.search(pattern, cleaned):
            return "neutral_info"

    if 'موجود' in cleaned and ('سعر' in cleaned or 'كم' in cleaned):
        return "neutral_info"

    if _is_menu_price_listing(text):
        return "neutral_info"

    return None


def _result_for_context(context, text):
    cleaned = clean_arabic_text(text).lower() if text else ""
    topic = "العروض والخصومات" if any(w in cleaned for w in ('سعر', 'دينار', 'خصم', 'عرض')) else "عام"

    if context == "positive_blessing":
        return {
            "sentiment": "إيجابي",
            "pos_score": 0.85,
            "neg_score": 0.05,
            "neu_score": 0.10,
            "topic": topic,
            "is_sarcastic": False,
            "sarcasm_explanation": "",
            "engine_used": "Context Rules (Blessing/Greeting)",
            "confidence": 0.92,
        }

    if context == "neutral_info":
        return {
            "sentiment": "محايد",
            "pos_score": 0.33,
            "neg_score": 0.33,
            "neu_score": 0.34,
            "topic": topic,
            "is_sarcastic": False,
            "sarcasm_explanation": "",
            "engine_used": "Context Rules (Price/Inquiry)",
            "confidence": 0.90,
        }

    return None


def _validate_sarcasm_result(text, data):
    """Post-process Gemini output to reject weak sarcasm classifications."""
    ctx = _classify_text_context(text)
    if ctx == "neutral_info":
        data["is_sarcastic"] = False
        data["sarcasm_explanation"] = ""
        data["final_sentiment"] = "محايد"
        return data
    if ctx == "positive_blessing":
        data["is_sarcastic"] = False
        data["sarcasm_explanation"] = ""
        data["final_sentiment"] = "إيجابي"
        return data

    if not data.get("is_sarcastic", False):
        return data

    explanation = (data.get("sarcasm_explanation") or "").strip()
    if not explanation:
        data["is_sarcastic"] = False
        data["sarcasm_explanation"] = ""
        return data

    explanation_lower = explanation.lower()
    false_sarcasm_signals = (
        'حسد', 'دعاء مبطن', 'غير رضا', 'مبطن', 'استياء مبطن',
        'سعر مبالغ', 'مبالغ فيه', 'سؤال بسيط',
    )
    if any(signal in explanation_lower for signal in false_sarcasm_signals):
        data["is_sarcastic"] = False
        data["sarcasm_explanation"] = ""
        if ctx == "positive_blessing":
            data["final_sentiment"] = "إيجابي"
        elif ctx == "neutral_info":
            data["final_sentiment"] = "محايد"
        return data

    final_sent = data.get("final_sentiment", "")
    if final_sent == "سلبي" and not _text_has_any_positive_sentiment(text):
        data["is_sarcastic"] = False
        data["sarcasm_explanation"] = ""
        return data

    return data



ARABIC_TOPIC_RULES = {

    "خدمة العملاء": [

        # الكلمات الأصلية

        "خدمه", "دعم", "عملاء", "موظف", "مساعده", "تواصل", "رد",

        # 25 كلمة جديدة

        "كول سنتر", "واتساب", "استجابة", "تفاعل", "شكوى", "استفسار", 

        "الموظفين", "الادارة", "مشرف", "معاملة", "اسلوب", "ردود", "هاتف", 

        "تيكت", "دعم فني", "مكالمة", "رفع طلب", "متابعة", "حل مشكلة", "صيانة", 

        "تجاوب", "اخلاق", "تعامل", "لباقة"

    ],

    "جودة المنتج": [

        # الكلمات الأصلية

        "جوده", "منتج", "خامه", "صنع", "شكل", "تغليف", "كرتون",

        # 25 كلمة جديدة

        "تصنيع", "مواد", "بلاستيك", "قماش", "ملمس", "طعم", "نكهة", "حجم", 

        "وزن", "مقاس", "لون", "طباعة", "خياطة", "متانة", "اصلي", "تقليد", 

        "ماركة", "ضمان", "عمر افتراضي", "مكونات", "حماية", "مظهر", "تفاصيل", 

        "مواصفات", "تصميم"

    ],

    "سرعة التوصيل": [

        # الكلمات الأصلية

        "توصيل", "شحن", "موعد", "تاخير", "سريع", "مندوب", "طلب", "تاخر",

        # 25 كلمة جديدة

        "شركة شحن", "ارامكس", "سمسا", "تتبع", "رقم الشحنة", "فرع", "استلام", 

        "تسليم", "موقع", "عنوان", "خريطة", "مستودع", "تجهيز", "قيد التنفيذ", 

        "تم الشحن", "مجاني", "رسوم توصيل", "وقت", "ايام عمل", "ساعات", 

        "مرسول", "جاهز", "وصول", "مسار", "شحنة"

    ],

    "العروض والخصومات": [

        # الكلمات الأصلية

        "سعر", "خصم", "عرض", "عروض", "تخفيض", "مكلف", "كوبون", "غالي",

        # 25 كلمة جديدة

        "كود", "كوبونات", "تخفيضات", "بلاك فرايدي", "مناسبة", "شحن مجاني", 

        "هدية", "مجانا", "عينة", "بوكس", "بكج", "مجموعة", "اقتصادي", "توفيري", 

        "غلاء", "ضريبة", "تكلفة", "رسوم اضافية", "ارخص", "اغلى", "سعر مناسب", 

        "قيمة", "تصفية", "بلاش", "فاتورة"

    ]

}



BASE_DIR_LEXICON = os.path.dirname(os.path.abspath(__file__))

POS_FILE = os.path.join(BASE_DIR_LEXICON, "positive_lexicon.txt")

NEG_FILE = os.path.join(BASE_DIR_LEXICON, "negative_lexicon.txt")

POS_ENG_FILE = os.path.join(BASE_DIR_LEXICON, "positive_eng.txt")

NEG_ENG_FILE = os.path.join(BASE_DIR_LEXICON, "negative_eng.txt")



def load_external_keywords(file_path):

    if os.path.exists(file_path):

        try:

            with open(file_path, "r", encoding="utf-8") as f:

                return [line.strip().lower() for line in f if line.strip() and not line.strip().startswith("#")]

        except Exception as e:

            print(f"Error loading lexicon {file_path}: {e}")

    return []



def detect_language(text):

    if not text:

        return "ar"

    # Count English (Latin) characters vs Arabic characters

    latin_chars = len(re.findall(r'[a-zA-Z]', text))

    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))

    if latin_chars > arabic_chars:

        return "en"

    return "ar"



def analyze_sentiment_english_local(text):
    cleaned = text.strip()
    if not cleaned:
        return {
            "sentiment": "محايد",
            "pos_score": 0.33,
            "neg_score": 0.33,
            "neu_score": 0.34,
            "topic": "عام",
            "is_sarcastic": False,
            "sarcasm_explanation": "",
            "engine_used": "Local English Fallback",
            "confidence": 0.50,
            "has_custom_match": False
        }
        
    # Load custom English keywords
    ext_pos = load_external_keywords(POS_ENG_FILE)
    ext_neg = load_external_keywords(NEG_ENG_FILE)
    
    # Check custom matches first with exact check
    has_pos_custom = check_custom_lexicon_match(cleaned, ext_pos)
    has_neg_custom = check_custom_lexicon_match(cleaned, ext_neg)
    
    has_custom_match = has_pos_custom or has_neg_custom
    
    if has_custom_match:
        pos_count = 0
        neg_count = 0
        
        # Exact count split words
        cleaned_lower = cleaned.lower()
        for char in ['.', ',', '!', '?', ';', ':', '(', ')', '[', ']', '{', '}', '-', '_', '"', "'"]:
            cleaned_lower = cleaned_lower.replace(char, ' ')
        cleaned_words = cleaned_lower.split()
        
        for word in cleaned_words:
            if word in ext_pos:
                pos_count += 1
            if word in ext_neg:
                neg_count += 1
                
        # Also check phrases
        padded = " " + " ".join(cleaned_words) + " "
        for p in ext_pos:
            if " " in p and f" {p} " in padded:
                pos_count += 1
        for n in ext_neg:
            if " " in n and f" {n} " in padded:
                neg_count += 1
                
        if pos_count > neg_count:
            label = "إيجابي"
            pos_score, neg_score, neu_score = 0.95, 0.02, 0.03
        elif neg_count > pos_count:
            label = "سلبي"
            pos_score, neg_score, neu_score = 0.02, 0.95, 0.03
        else:
            label = "محايد"
            pos_score, neg_score, neu_score = 0.45, 0.45, 0.10
            
        return {
            "sentiment": label,
            "pos_score": pos_score,
            "neg_score": neg_score,
            "neu_score": neu_score,
            "topic": "عام",
            "is_sarcastic": False,
            "sarcasm_explanation": "",
            "engine_used": "Local English Lexicon (Custom Match)",
            "confidence": 0.95,
            "has_custom_match": True
        }
        
    # VADER offline analyzer
    if HAS_NLTK_VADER:
        try:
            sia = SentimentIntensityAnalyzer()
            scores = sia.polarity_scores(cleaned)
            compound = scores.get("compound", 0.0)
            
            if compound >= 0.05:
                label = "إيجابي"
            elif compound <= -0.05:
                label = "سلبي"
            else:
                label = "محايد"
                
            return {
                "sentiment": label,
                "pos_score": round(scores.get("pos", 0.0), 2),
                "neg_score": round(scores.get("neg", 0.0), 2),
                "neu_score": round(scores.get("neu", 1.0), 2),
                "topic": "عام",
                "is_sarcastic": False,
                "sarcasm_explanation": "",
                "engine_used": "Offline VADER Engine (NLTK)",
                "confidence": 0.90,
                "has_custom_match": False
            }
        except Exception as e:
            print(f"Error running VADER: {e}")
            
    # Default fallback
    return {
        "sentiment": "محايد",
        "pos_score": 0.33,
        "neg_score": 0.33,
        "neu_score": 0.34,
        "topic": "عام",
        "is_sarcastic": False,
        "sarcasm_explanation": "",
        "engine_used": "Local English Fallback",
        "confidence": 0.50,
        "has_custom_match": False
    }
def check_custom_lexicon_match(cleaned_text, lexicon):
    if not cleaned_text:
        return False
    # Clean text to remove basic punctuation that might cling to words
    cleaned_lower = cleaned_text.lower()
    for char in ['.', ',', '!', '?', ';', ':', '(', ')', '[', ']', '{', '}', '-', '_', '"', "'"]:
        cleaned_lower = cleaned_lower.replace(char, ' ')
    
    cleaned_words = cleaned_lower.split()
    word_set = set(cleaned_words)
    padded_text = " " + " ".join(cleaned_words) + " "
    
    for entry in lexicon:
        entry = entry.strip().lower()
        if not entry or len(entry) <= 1:
            continue
        # Skip pure symbols/emojis for custom match bypass to avoid false triggers
        if not any(c.isalnum() for c in entry):
            continue
        
        if " " in entry:
            # Multi-word phrase exact match using padding
            if f" {entry} " in padded_text:
                return True
        else:
            # Single-word exact match using set lookup
            if entry in word_set:
                return True
    return False


def light_stem_arabic(word):
    word = word.strip().lower()
    if len(word) <= 3:
        return word
        
    # Remove common prefixes
    prefixes = ['ال', 'وال', 'بال', 'كال', 'فال', 'لل', 'وبال', 'ولل']
    for pref in prefixes:
        if word.startswith(pref) and len(word) - len(pref) >= 3:
            word = word[len(pref):]
            break
            
    # Remove leading 'و', 'ب', 'ف', 'ل' if word has >= 4 chars
    for pref in ['و', 'ب', 'ف', 'ل']:
        if word.startswith(pref) and len(word) >= 4:
            word = word[1:]
            break
            
    # Remove common suffixes
    suffixes = ['ها', 'هم', 'هن', 'كما', 'كم', 'نا', 'ات', 'ون', 'ين', 'ية', 'يه', 'ة', 'ه', 'ي']
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            word = word[:-len(suf)]
            break
            
    return word


def analyze_sentiment_local(text):
    if not text or not text.strip():
        return {
            "sentiment": "محايد",
            "pos_score": 0.33,
            "neg_score": 0.33,
            "neu_score": 0.34,
            "topic": "عام",
            "is_sarcastic": False,
            "sarcasm_explanation": "",
            "engine_used": "Local Lexicon Engine (Offline)",
            "confidence": 0.50
        }

    ctx = _classify_text_context(text)
    if ctx:
        return _result_for_context(ctx, text)
        
    cleaned = clean_arabic_text(text).lower()
    
    # Load external dynamic keywords
    ext_pos = load_external_keywords(POS_FILE)
    ext_neg = load_external_keywords(NEG_FILE)
    
    all_pos = list(set(ARABIC_POSITIVE_KEYWORDS + ext_pos))
    all_neg = list(set(ARABIC_NEGATIVE_KEYWORDS + ext_neg))
    
    # Separate into phrases and single words
    pos_phrases = [p for p in all_pos if " " in p]
    pos_singles = {light_stem_arabic(p) for p in all_pos if " " not in p}
    
    neg_phrases = [n for n in all_neg if " " in n]
    neg_singles = {light_stem_arabic(n) for n in all_neg if " " not in n}
    
    ARABIC_NEGATIONS = {'مش', 'مو', 'ما', 'لم', 'لن', 'لا', 'ليس', 'غير', 'بدون', 'بلا', 'مب', 'ماني', 'مافي'}
    ARABIC_INTENSIFIERS = {'جدا', 'كثيرا', 'كتير', 'عنجد', 'شديد', 'قوي', 'كتيرر', 'جداا', 'للغاية', 'بشدة', 'موت', 'خرافي', 'رهيب'}
    ARABIC_LAUGHS = {'هههه', 'ههه', 'ههههه', 'هههههه', 'ههههههه', 'هع'}
    
    pos_match_score = 0.0
    neg_match_score = 0.0
    
    # 1. Match phrases first to prevent sub-parts matching
    temp_text = cleaned
    # Remove basic punctuation first for exact phrase checking
    for char in ['.', ',', '!', '?', ';', ':', '(', ')', '[', ']', '{', '}', '-', '_', '"', "'"]:
        temp_text = temp_text.replace(char, ' ')
        
    temp_words = temp_text.split()
    padded_temp = " " + " ".join(temp_words) + " "
    
    for phrase in pos_phrases:
        phrase_stripped = phrase.strip().lower()
        if not phrase_stripped:
            continue
        target = f" {phrase_stripped} "
        matches = padded_temp.count(target)
        if matches > 0:
            pos_match_score += matches * 1.5
            padded_temp = padded_temp.replace(target, " ")
            
    for phrase in neg_phrases:
        phrase_stripped = phrase.strip().lower()
        if not phrase_stripped:
            continue
        target = f" {phrase_stripped} "
        matches = padded_temp.count(target)
        if matches > 0:
            neg_match_score += matches * 1.5
            padded_temp = padded_temp.replace(target, " ")
            
    # 2. Tokenize and match single words
    tokens = padded_temp.split()
    num_tokens = len(tokens)
    
    for i, token in enumerate(tokens):
        stemmed = light_stem_arabic(token)
        
        is_pos_match = token in all_pos or (len(stemmed) >= MIN_STEM_MATCH_LEN and stemmed in pos_singles)
        is_neg_match = token in all_neg or (len(stemmed) >= MIN_STEM_MATCH_LEN and stemmed in neg_singles)
        
        if is_pos_match:
            negated = False
            for j in range(max(0, i-2), i):
                if tokens[j] in ARABIC_NEGATIONS:
                    negated = True
                    break
            
            intensified = False
            if (i > 0 and tokens[i-1] in ARABIC_INTENSIFIERS) or (i < num_tokens - 1 and tokens[i+1] in ARABIC_INTENSIFIERS):
                intensified = True
                
            weight = 1.5 if intensified else 1.0
            if negated:
                neg_match_score += weight
            else:
                pos_match_score += weight
                
        elif is_neg_match:
            negated = False
            for j in range(max(0, i-2), i):
                if tokens[j] in ARABIC_NEGATIONS:
                    negated = True
                    break
                    
            intensified = False
            if (i > 0 and tokens[i-1] in ARABIC_INTENSIFIERS) or (i < num_tokens - 1 and tokens[i+1] in ARABIC_INTENSIFIERS):
                intensified = True
                
            weight = 1.5 if intensified else 1.0
            if negated:
                pos_match_score += weight
            else:
                neg_match_score += weight
                
    # 3. Conservative Local Sarcasm Engine — only clear ironic patterns
    is_sarcastic = False
    sarcasm_explanation = ""

    has_hyperbolic_praise = _text_has_hyperbolic_praise(cleaned) or pos_match_score >= 1.5
    has_negation = any(neg in tokens for neg in ARABIC_NEGATIONS)
    has_degree_trigger = any(trigger in cleaned for trigger in SARCASM_DEGREE_TRIGGERS)

    # Rule B: Laughing + ironic praise (not plain complaint with laugh)
    has_laugh = any(
        token in ARABIC_LAUGHS or any(laugh in token for laugh in ['هههه', 'ههه'])
        for token in tokens
    )
    if has_laugh and neg_match_score >= 1.5 and pos_match_score >= 1.0:
        is_sarcastic = True
        sarcasm_explanation = "ضحك مع مديح ساخر: نبرة تهكمية وليست شكوى مباشرة."

    # Rule C: Praise + "لدرجة" + negation (e.g. "ممتاز لدرجة ما بشتغل", "سريعة لدرجة ما بتفتح")
    if has_degree_trigger and has_negation and (has_hyperbolic_praise or pos_match_score >= 1.0):
        is_sarcastic = True
        sarcasm_explanation = "مديح متبوع بنفي وظيفة أساسية عبر «لدرجة» — نمط تهكم واضح."

    # Rule D: Praise + ironic emoji + negative context (e.g. "شغال دفّاية بالصيف 🔥")
    has_ironic_emoji = any(emoji in text for emoji in SARCASM_IRONIC_EMOJIS)
    has_surface_praise = pos_match_score >= 1.0 or any(word in cleaned for word in SARCASM_SURFACE_PRAISE)
    has_negative_context = (
        neg_match_score >= 0.5
        or any(metaphor in cleaned for metaphor in SARCASM_NEGATIVE_METAPHORS)
    )
    if has_ironic_emoji and has_surface_praise and has_negative_context:
        is_sarcastic = True
        sarcasm_explanation = "مديح ظاهري مع سياق سلبي ورمز ساخر — تهكم واضح."

    # Calculate scores and label (sarcasm flag is independent; no forced sentiment inversion)
    total_score = pos_match_score + neg_match_score
    if total_score == 0:
        label = "محايد"
        pos_pct, neg_pct, neu_pct = 0.33, 0.33, 0.34
    elif pos_match_score > neg_match_score:
        label = "إيجابي"
        pos_pct = round(pos_match_score / total_score, 2)
        pos_pct = min(0.95, max(0.5, pos_pct))
        neg_pct = round((1.0 - pos_pct) / 2, 2)
        neu_pct = round(1.0 - pos_pct - neg_pct, 2)
    elif neg_match_score > pos_match_score:
        label = "سلبي"
        neg_pct = round(neg_match_score / total_score, 2)
        neg_pct = min(0.95, max(0.5, neg_pct))
        pos_pct = round((1.0 - neg_pct) / 2, 2)
        neu_pct = round(1.0 - pos_pct - neg_pct, 2)
    else:
        label = "محايد"
        pos_pct, neg_pct, neu_pct = 0.33, 0.33, 0.34

    # Confirmed sarcasm carries a negative true meaning (without broad score inversion)
    if is_sarcastic and label == "إيجابي":
        label = "سلبي"
        neg_pct = max(neg_pct, 0.65)
        pos_pct = min(pos_pct, 0.20)
        neu_pct = round(1.0 - pos_pct - neg_pct, 2)
        
    # Determine topic
    detected_topic = "عام"
    for topic, keywords in ARABIC_TOPIC_RULES.items():
        if any(kw in cleaned for kw in keywords):
            detected_topic = topic
            break
            
    engine_used = "Local Lexicon + Sarcasm Engine" if is_sarcastic else "Local Lexicon Engine (Offline)"
    confidence = 0.90 if is_sarcastic else (0.85 if total_score > 0 else 0.50)
    
    return {
        "sentiment": label,
        "pos_score": pos_pct,
        "neg_score": neg_pct,
        "neu_score": neu_pct,
        "topic": detected_topic,
        "is_sarcastic": is_sarcastic,
        "sarcasm_explanation": sarcasm_explanation,
        "engine_used": engine_used,
        "confidence": confidence
    }
# ==========================================

# 3. ONLINE ADVANCED AI TIER (GEMINI API)

# ==========================================

def get_ai_topic_modeling(text, api_key=None):
    if not HAS_GEMINI_SDK or not api_key or not text or not text.strip():
        return {"topic": "عام", "keywords": []}
        
    genai.configure(api_key=api_key)
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    prompt = f"""
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
    """
    
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
    
    prompt = f"""
    أنت محلل مشاعر متوازن متخصص في تحليل الآراء على منصات التواصل الاجتماعي باللهجات العربية (الشامية، المصرية، الخليجية).
    
    قم بتحليل النص التالي بدقة مع الأخذ في الاعتبار أن التصنيف المحلي المبدئي للمشاعر هو: "{local_sentiment}".
    
    النص المراد تحليله: "{text}"
    
    قواعد مهمة للتهكم (Sarcasm) — كن محافظاً وتجنب الإيجابيات الكاذبة:
    - لا تضع is_sarcastic=true إلا إذا كان التهكم واضحاً ولا يُفسر المعنى إلا على أنه سخرية.
    - لا تعتبر شكوى مباشرة، مراجعة مختلطة، أو نقداً بنّاءً تهكماً.
    - لا تعتبر دعاءً أو تهنئة أو بركة تهكماً أبداً (مثل: "الله يفتحها عليكم"، "اية الرزق").
    - لا تعتبر استفسار سعر أو توفر منتج سلبياً أو ساخراً (مثل: "كم سعر..."، "موجود كبة وكم سعرها"، "كيف الاسعار").
    - لا تعتبر إعلان قائمة أسعار/منيو تهكماً (مثل: "سدر منسف 15 دينار") ما لم يُذكر استياء صريح.
    - أمثلة ليست تهكماً: "الخدمة جيدة لكن بطيئة"، "ما رضيت عن المنتج"، "سريع بس ما بفتح".
    - أمثلة تهكم حقيقي: "اللابتوب شغال دفّاية بالصيف"، "خدمة سريعة لدرجة ما بتفتح"، "ممتاز لدرجة ما بشتغل".
    - final_sentiment يُحدّد حسب المعنى الحقيقي؛ النص السلبي الصريح ليس بالضرورة تهكماً.
    - إذا كان is_sarcastic=true فيجب أن يكون sarcasm_explanation غير فارغ ويوضّح سبب التهكم.
    
    المطلوب استخراجه:
    1. final_sentiment: تحديد المشاعر النهائية (إيجابي، سلبي، أو محايد).
    2. pos_score: درجة الإيجابية كقيمة عشرية بين 0.0 و 1.0.
    3. neg_score: درجة السلبية كقيمة عشرية بين 0.0 و 1.0.
    4. neu_score: درجة الحياد كقيمة عشرية بين 0.0 و 1.0.
    (ملاحظة: مجموع الدرجات الثلاث يجب أن يكون قريباً جداً من 1.0).
    5. is_sarcastic: true فقط للتهكم الواضح، وإلا false.
    6. sarcasm_explanation: شرح مختصر بالعربية لسبب التهكم إن وُجد، وإلا "".
    7. topic: تصنيف موضوع النص بكلمة أو اثنتين فقط (مثال: خدمة عملاء، جودة منتج، سرعة توصيل، أسعار وعروض، إلخ).
    8. keywords: قائمة تحتوي على أهم 3 كلمات مفتاحية في النص.
    
    يجب أن تكون المخرجات عبارة عن كود JSON صالح تماماً فقط باللغة العربية، دون أي نصوص إضافية أو علامات Markdown أو ```json.
    
    صيغة الـ JSON المطلوبة:
    {{
      "final_sentiment": "إيجابي/سلبي/محايد",
      "pos_score": 0.1,
      "neg_score": 0.8,
      "neu_score": 0.1,
      "is_sarcastic": false,
      "sarcasm_explanation": "",
      "topic": "موضوع النص",
      "keywords": ["كلمة1", "كلمة2", "كلمة3"]
    }}
    """
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_txt)
            data = _validate_sarcasm_result(text, data)
            
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
            
    return None


def batch_ai_topic_modeling(posts_data, api_key=None):
    if not HAS_GEMINI_SDK:
        raise Exception("حزمة google-generativeai غير مثبتة في بيئة تشغيل الخادم (Django Environment).")
    if not api_key:
        raise Exception("مفتاح API الخاص بـ Gemini (GEMINI_API_KEY) مفقود في بيئة تشغيل الخادم.")
    if not posts_data:
        return []
        
    print(f"🧠 [Batch AI] Sending {len(posts_data)} posts to Gemini for topic classification...")
    genai.configure(api_key=api_key)
    model_names = ['gemini-2.0-flash', 'gemini-1.5-flash']
    
    input_json = json.dumps(posts_data, ensure_ascii=False, indent=2)
    
    prompt = f"""
    أنت خبير تصنيف موضوعات وتحليل نصوص باللغة العربية.
    لديك قائمة من المنشورات بصيغة JSON تحتوي على المعرف (id) والمحتوى (content).
    المطلوب: قم بتحليل محتوى كل منشور بدقة، واستخراج الموضوع الأساسي (topic) وأهم 3 كلمات مفتاحية (keywords).
    
    شروط تصنيف الموضوع الأساسي (topic):
    - اختر اسماً دقيقاً وموجزاً جداً للموضوع بكلمة أو اثنتين فقط (مثال: خدمة عملاء، جودة منتج، سرعة توصيل، أسعار وعروض، إعلانات، قضايا فنية، مقاطعة، دعم انتخابي، إلخ).
    
    المدخلات:
    {input_json}
    
    المخرجات المطلوبة:
    أعد النتيجة كـ JSON Array صالح فقط دون أي علامات Markdown أو نصوص إضافية، بالصيغة التالية تماماً:
    [
      {{
        "id": 123,
        "topic": "اسم الموضوع",
        "keywords": ["كلمة1", "كلمة2", "كلمة3"]
      }}
    ]
    """
    
    errors = []
    for name in model_names:
        try:
            print(f"   💬 [Batch AI] Trying model {name}...")
            model = genai.GenerativeModel(name)
            response = model.generate_content(prompt)
            print(f"   ✅ [Batch AI] Received response from {name}. Parsing JSON...")
            clean_txt = response.text.replace("```json", "").replace("```", "").strip()
            start_idx = clean_txt.find('[')
            end_idx = clean_txt.rfind(']')
            if start_idx != -1 and end_idx != -1:
                clean_txt = clean_txt[start_idx:end_idx+1]
            data = json.loads(clean_txt)
            if isinstance(data, list):
                print(f"   🎉 [Batch AI] Successfully parsed {len(data)} classified topics!")
                return data
        except Exception as e:
            err_msg = f"{name}: {str(e)}"
            print(f"   ⚠️ [Batch AI] Model failed - {err_msg}")
            errors.append(err_msg)
            continue
            
    raise Exception(f"فشلت جميع محاولات تصنيف المواضيع عبر Gemini. الأخطاء: {'; '.join(errors)}")


def analyze_text_hybrid(text, parent_text=None, inherited_topic=None):
    is_comment = True
    if not text or not text.strip():
        return analyze_sentiment_local("")
        
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("ai_key")
    is_sarcastic = False
    sarcasm_explanation = ""
    engine_used = "Local Lexicon Engine"
    local_confidence = 0.70
    
    # Step 1: Language Detection
    lang = detect_language(text)
    
    # Step 2: Local Keyword Matching & Local Analysis
    has_custom_match = False
    
    if lang == "en":
        # English execution path
        local_res = analyze_sentiment_english_local(text)
        has_custom_match = local_res.get("has_custom_match", False)
        
        local_sentiment = local_res["sentiment"]
        pos_score = local_res["pos_score"]
        neg_score = local_res["neg_score"]
        neu_score = local_res["neu_score"]
        local_confidence = local_res["confidence"]
        engine_used = local_res["engine_used"]
        is_sarcastic = local_res.get("is_sarcastic", False)
        sarcasm_explanation = local_res.get("sarcasm_explanation", "")
        cleaned = text.strip()
    else:
        # Arabic execution path
        cleaned = clean_arabic_text(text)
        local_pipeline = get_marbert_pipeline()
        
        local_sentiment = "محايد"
        local_confidence = 0.70
        pos_score, neg_score, neu_score = 0.33, 0.33, 0.34
        engine_used = "Local Lexicon Engine"
        
        if local_pipeline:
            try:
                res = local_pipeline(cleaned)[0]
                label_mapping = {
                    "LABEL_0": "سلبي",
                    "LABEL_1": "محايد",
                    "LABEL_2": "إيجابي"
                }
                local_sentiment = label_mapping.get(res['label'], "محايد")
                local_confidence = res['score']
                
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
                local_confidence = lex_res.get("confidence", 0.70)
                engine_used = lex_res.get("engine_used", "Local Lexicon (Fallback)")
                is_sarcastic = lex_res.get("is_sarcastic", False)
                sarcasm_explanation = lex_res.get("sarcasm_explanation", "")
        else:
            lex_res = analyze_sentiment_local(cleaned)
            local_sentiment = lex_res["sentiment"]
            pos_score, neg_score, neu_score = lex_res["pos_score"], lex_res["neg_score"], lex_res["neu_score"]
            local_confidence = lex_res.get("confidence", 0.70)
            engine_used = lex_res.get("engine_used", "Local Lexicon (Offline)")
            is_sarcastic = lex_res.get("is_sarcastic", False)
            sarcasm_explanation = lex_res.get("sarcasm_explanation", "")
            
        # Load dynamic lexicon keywords to check if the user's custom dictionary was matched
        ext_pos = load_external_keywords(POS_FILE)
        ext_neg = load_external_keywords(NEG_FILE)
        
        has_custom_match = check_custom_lexicon_match(cleaned, ext_pos) or check_custom_lexicon_match(cleaned, ext_neg)
        
        if has_custom_match:
            local_confidence = 0.95
            if "MARBERT" in engine_used:
                engine_used = "Local MARBERT (Custom Match)"
            else:
                engine_used = "Local Lexicon (Custom Match)"
                
    # Step 3: Topic Modeling (Inherit parent post's topic, fallback to local keyword rules)
    detected_topic = "عام"
    keywords = []
    
    if inherited_topic:
        detected_topic = inherited_topic
    else:
        for topic, keywords_list in ARABIC_TOPIC_RULES.items():
            if any(kw in cleaned.lower() for kw in keywords_list):
                detected_topic = topic
                break
                
    # Step 4: Fallback to Gemini for deep analysis (Only for comments with low confidence, AND ONLY if no custom keyword match!)
    final_sentiment = local_sentiment
    
    # Minimize AI reliance: only fall back to Gemini for comments that are moderately long (word count > 3)
    # and have low local confidence (less than 0.60), bypassing fallback entirely for simple/short/confident offline ones.
    word_count = len(cleaned.split()) if cleaned else 0
    skip_gemini_ctx = _classify_text_context(text) in ("neutral_info", "positive_blessing")
    if (
        is_comment
        and not has_custom_match
        and not skip_gemini_ctx
        and word_count > 3
        and (local_confidence < 0.60)
        and api_key
        and HAS_GEMINI_SDK
    ):
        advanced_res = analyze_complex_sentiment(cleaned, local_sentiment, api_key)
        time.sleep(1)
        if advanced_res:
            final_sentiment = advanced_res.get("final_sentiment", final_sentiment)
            pos_score = advanced_res.get("pos_score", pos_score)
            neg_score = advanced_res.get("neg_score", neg_score)
            neu_score = advanced_res.get("neu_score", neu_score)
            is_sarcastic = advanced_res.get("is_sarcastic", False)
            sarcasm_explanation = advanced_res.get("sarcasm_explanation", "")
            detected_topic = advanced_res.get("topic", detected_topic)
            keywords = advanced_res.get("keywords", keywords)
            
            model_used = advanced_res.get("_model_used", "gemini-1.5-flash")
            pres_name = "Gemini 2.0 Flash" if "2.0" in model_used else "Gemini 1.5 Flash"
            engine_used = f"{pres_name} (Sarcasm Fallback)"
            local_confidence = 0.95

    ctx_override = _classify_text_context(text)
    if ctx_override:
        ctx_res = _result_for_context(ctx_override, text)
        final_sentiment = ctx_res["sentiment"]
        pos_score = ctx_res["pos_score"]
        neg_score = ctx_res["neg_score"]
        neu_score = ctx_res["neu_score"]
        is_sarcastic = False
        sarcasm_explanation = ""
        if detected_topic == "عام":
            detected_topic = ctx_res["topic"]
        engine_used = ctx_res["engine_used"]
        local_confidence = ctx_res["confidence"]
            
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
        "keywords": keywords,
        "lang_processed": lang
    }
def bulk_analyze_posts(posts_qs, batch=None):

    try:
        from .models import SentimentResult, TopicTag, AIModel
    except ImportError:
        try:
            from api_app.models import SentimentResult, TopicTag, AIModel
        except ImportError:
            from core.api_app.models import SentimentResult, TopicTag, AIModel


    

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
    newly_analyzed_parents = []

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

        # Check if this is a parent post (not a comment)
        is_parent_post = (post.parent_post is None) or (post.media_type in ['post', 'منشور'])

        if is_parent_post:
            # Parent posts are always classified as Neutral (محايد) for sentiment
            # Blazing-fast offline local topic modeling!
            detected_topic = "عام"
            keywords = []
            
            cleaned = clean_arabic_text(post.content) if post.content else ""
            for topic, keywords_list in ARABIC_TOPIC_RULES.items():
                if any(kw in cleaned.lower() for kw in keywords_list):
                    detected_topic = topic
                    break
                        
            res = {
                "sentiment": "محايد",
                "pos_score": 0.0,
                "neg_score": 0.0,
                "neu_score": 1.0,
                "is_sarcastic": False,
                "sarcasm_explanation": "",
                "engine_used": "System Rule",
                "confidence": 1.0,
                "topic": detected_topic,
                "keywords": keywords
            }
        else:
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

        

        # 2. Save TopicTag (Only for parent posts)

        if is_parent_post:

            TopicTag.objects.create(

                result=sentiment_obj,

                topic_label=res.get("topic", "عام"),

                confidence=0.90

            )

            newly_analyzed_parents.append(post)

        

        analyzed_count += 1

        

    # Phase 2: Batch AI Topic Modeling for newly analyzed parent posts
    if newly_analyzed_parents:
        import os
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("ai_key")
        if api_key and HAS_GEMINI_SDK:
            print(f"Running batch AI topic modeling for {len(newly_analyzed_parents)} parent posts...")
            posts_data = [{"id": p.id, "content": p.content[:400]} for p in newly_analyzed_parents]
            try:
                batch_results = batch_ai_topic_modeling(posts_data, api_key)
                # Create a lookup map of id -> result (handling string/int keys)
                results_map = {}
                for item in batch_results:
                    if "id" in item:
                        try:
                            results_map[int(item["id"])] = item
                        except (ValueError, TypeError):
                            results_map[item["id"]] = item
                
                # Update the TopicTags in the database
                for post in newly_analyzed_parents:
                    ai_res = results_map.get(post.id)
                    if ai_res:
                        ai_topic = ai_res.get("topic", "عام")
                        # Find the TopicTag for this post's sentiment result
                        sent_res = post.sentiments.first()
                        if sent_res:
                            # Update engine_used to mark it as analyzed by Gemini Topic modeling, preventing any re-sending!
                            sent_res.engine_used = "Gemini 2.0 Flash (Batch Topic)"
                            sent_res.save()
                            
                            tag = sent_res.tags.first()
                            if tag:
                                tag.topic_label = ai_topic
                                tag.save()
                                print(f"   [Batch AI Update] Updated Post ID {post.id} topic to '{ai_topic}' and engine to 'Gemini 2.0 Flash (Batch Topic)'")
            except Exception as e:
                print(f"Error during batch AI topic modeling update: {e}")

    print(f"Finished bulk analysis! Total analyzed: {analyzed_count}")

    return analyzed_count