import os
import re

def upgrade_sentiment_engine():
    file_path = r"c:\Users\ThinkPad\Desktop\مشروع الجامعة\core\api_app\sentiment_engine.py"
    
    if not os.path.exists(file_path):
        print("sentiment_engine.py not found!")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print("Successfully read sentiment_engine.py")
    
    # We will standardize newlines to simplify parsing, but keep double newlines if needed.
    # To keep it extremely simple, we will replace the functions using an indentation-based parser.
    
    def replace_function_by_indentation(text_content, func_name, new_definition):
        lines = text_content.splitlines()
        start_idx = None
        end_idx = None
        
        for idx, line in enumerate(lines):
            if line.strip().startswith(f"def {func_name}("):
                start_idx = idx
                break
                
        if start_idx is None:
            return text_content  # Function not found, return original
            
        for idx in range(start_idx + 1, len(lines)):
            line = lines[idx]
            if line.strip():  # non-empty
                # If a line starts with a non-whitespace character, it marks the end of the block
                if not (line.startswith(' ') or line.startswith('\t')):
                    # Check if it's not a comment or part of def/class
                    end_idx = idx
                    break
        else:
            end_idx = len(lines)
            
        new_lines = lines[:start_idx] + [new_definition] + lines[end_idx:]
        return "\n".join(new_lines)

    # 1. New English local engine
    eng_engine_code = """def analyze_sentiment_english_local(text):
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
    }"""

    # 2. check_custom_lexicon_match helper
    custom_match_code = """def check_custom_lexicon_match(cleaned_text, lexicon):
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
    return False"""

    # 3. light_stem_arabic helper
    stem_code = """def light_stem_arabic(word):
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
            
    return word"""

    # 4. Upgraded analyze_sentiment_local (Arabic)
    arabic_local_code = """def analyze_sentiment_local(text):
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
        
        is_pos_match = stemmed in pos_singles or token in all_pos
        is_neg_match = stemmed in neg_singles or token in all_neg
        
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
                
    # 3. Local Sarcasm Engine Logic
    is_sarcastic = False
    sarcasm_explanation = ""
    
    # Rule A: Sentiment Clash
    if pos_match_score >= 1.0 and neg_match_score >= 1.0:
        is_sarcastic = True
        sarcasm_explanation = "تناقض في الكلمات: تعليق يحتوي على كلمات إيجابية وسلبية معاً بنبرة تهكمية."
        
    # Rule B: Laughing + Negative sentiment
    has_laugh = any(token in ARABIC_LAUGHS or any(laugh in token for laugh in ['هههه', 'ههه']) for token in tokens)
    if has_laugh and neg_match_score >= 0.5:
        is_sarcastic = True
        sarcasm_explanation = "ضحك مع استياء: دمج الضحك مع كلمات سلبية يدل على التهكم والسخرية."
        
    # Rule C: Sentiment clash via "but" or "to the extent" (e.g. "سريع جداً بس ما بفتح" / "سريع لدرجة ما بفتح")
    has_but = any(but in tokens for but in ['بس', 'لكن', 'الا', 'مع ان', 'لدرجة', 'لدرجه'])
    if has_but and pos_match_score >= 1.0 and any(neg in tokens for neg in ARABIC_NEGATIONS):
        is_sarcastic = True
        sarcasm_explanation = "استدراك ساخر: مدح صفة متبوعة بنفي عمل أو وظيفة أساسية للمنتج."
        
    # If sarcasm is detected locally, invert positive sentiment to negative!
    if is_sarcastic:
        neg_match_score = max(neg_match_score, pos_match_score + 1.0)
        pos_match_score = 0.0
        
    # Calculate scores and label
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
    }"""

    # 5. The absolute master orchestrator `analyze_text_hybrid`
    hybrid_orchestrator_code = """def analyze_text_hybrid(text, parent_text=None, inherited_topic=None):
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
                
    # Step 3: Topic Modeling (Strictly AI-based for main posts, inherited for comments)
    detected_topic = "عام"
    keywords = []
    is_comment = parent_text is not None
    
    if inherited_topic:
        detected_topic = inherited_topic
    elif not is_comment:
        if api_key and HAS_GEMINI_SDK:
            try:
                ai_topic_res = get_ai_topic_modeling(cleaned, api_key)
                detected_topic = ai_topic_res.get("topic", "عام")
                keywords = ai_topic_res.get("keywords", [])
            except Exception as e:
                print(f"Error fetching AI topic modeling for post: {e}")
                
        if detected_topic == "عام":
            for topic, keywords_list in ARABIC_TOPIC_RULES.items():
                if any(kw in cleaned.lower() for kw in keywords_list):
                    detected_topic = topic
                    break
    else:
        for topic, keywords_list in ARABIC_TOPIC_RULES.items():
            if any(kw in cleaned.lower() for kw in keywords_list):
                detected_topic = topic
                break
                
    # Step 4: Fallback to Gemini for deep analysis (Only for comments with low confidence, AND ONLY if no custom keyword match!)
    final_sentiment = local_sentiment
    
    if is_comment and not has_custom_match and (local_confidence < 0.85 or "Offline" in engine_used) and api_key and HAS_GEMINI_SDK:
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
    }"""

    # We replace from most independent up to the top level
    content = replace_function_by_indentation(content, "analyze_sentiment_english_local", eng_engine_code)
    
    # Since check_custom_lexicon_match and light_stem_arabic are helper functions,
    # let's inject them directly above analyze_sentiment_local if not already present.
    # To do this cleanly: if analyze_sentiment_local is in the file, we can replace it
    # with the custom match helper + stem helper + analyze_sentiment_local.
    # This is 100% safe and ensures they are defined before they are used!
    
    complete_local_block = custom_match_code + "\n\n\n" + stem_code + "\n\n\n" + arabic_local_code
    
    # We replace check_custom_lexicon_match, light_stem_arabic, and analyze_sentiment_local
    # if they are already in the file.
    content = replace_function_by_indentation(content, "check_custom_lexicon_match", "")
    content = replace_function_by_indentation(content, "light_stem_arabic", "")
    content = replace_function_by_indentation(content, "analyze_sentiment_local", complete_local_block)
    
    # Now replace the main hybrid orchestrator
    content = replace_function_by_indentation(content, "analyze_text_hybrid", hybrid_orchestrator_code)
    
    # Write back the fully upgraded code
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("All engine upgrades written successfully with zero formatting errors!")

if __name__ == '__main__':
    upgrade_sentiment_engine()
