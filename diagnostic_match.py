import os
from api_app.sentiment_engine import clean_arabic_text, load_external_keywords, POS_FILE, NEG_FILE

def test_match():
    text = "اللابتوب شغال دفّاية بالصيف! 🔥"
    cleaned = clean_arabic_text(text).lower()
    
    ext_pos = load_external_keywords(POS_FILE)
    ext_neg = load_external_keywords(NEG_FILE)
    
    matched_pos = [word for word in ext_pos if word in cleaned]
    matched_neg = [word for word in ext_neg if word in cleaned]
    
    print("Cleaned text:", cleaned)
    print("Matched positive keywords in lexicon:", matched_pos)
    print("Matched negative keywords in lexicon:", matched_neg)

if __name__ == '__main__':
    test_match()
