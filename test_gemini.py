import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.sentiment_engine import analyze_text_hybrid, HAS_GEMINI_SDK

def test():
    print("=========================================")
    print("DIAGNOSTIC TEST FOR ARABIC SENTIMENT SYSTEM")
    print("=========================================")
    
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("ai_key")
    print(f"1. Gemini SDK Installed: {HAS_GEMINI_SDK}")
    print(f"2. Gemini API Key Present: {api_key is not None}")
    if api_key:
        print(f"   Key length: {len(api_key)}")
        print(f"   Key starts with: {api_key[:8]}...")
    
    # Test 1: Sarcastic Comment (triggers Gemini Sarcasm Fallback)
    test_comment = "اللابتوب شغال دفّاية بالصيف! 🔥"
    parent_post = "اشتريت هذا اللابتوب الجديد اليوم"
    print(f"\n3. Testing sarcastic comment: '{test_comment}'")
    print(f"   Parent Post: '{parent_post}'")
    
    try:
        res = analyze_text_hybrid(test_comment, parent_text=parent_post)
        print("\n4. COMMENT ANALYSIS RESULT (Gemini Sarcasm Fallback):")
        print(f"   Sentiment: {res.get('sentiment')}")
        print(f"   Engine Used: {res.get('engine_used')}")
        print(f"   Is Sarcastic: {res.get('is_sarcastic')}")
        print(f"   Sarcasm Explanation: {res.get('sarcasm_explanation')}")
        print(f"   Topic: {res.get('topic')}")
        print(f"   Confidence: {res.get('confidence')}")
        print(f"   Keywords: {res.get('keywords')}")
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR DURING COMMENT ANALYSIS: {e}")
        import traceback
        traceback.print_exc()
        
    # Test 2: Main Post (triggers Local Sentiment + Gemini Topic Modeling)
    test_post = "الخدمة سريعة لدرجة إنها ما بتفتح!"
    print(f"\n=========================================")
    print(f"5. Testing main post: '{test_post}'")
    
    try:
        res = analyze_text_hybrid(test_post)
        print("\n6. MAIN POST ANALYSIS RESULT (Offline Sentiment + Gemini Topic):")
        print(f"   Sentiment: {res.get('sentiment')}")
        print(f"   Engine Used: {res.get('engine_used')}")
        print(f"   Is Sarcastic: {res.get('is_sarcastic')}")
        print(f"   Topic: {res.get('topic')}")
        print(f"   Confidence: {res.get('confidence')}")
        print(f"   Keywords: {res.get('keywords')}")
    except Exception as e:
        print(f"\n❌ RUNTIME ERROR DURING POST ANALYSIS: {e}")
        
    print("=========================================")

if __name__ == '__main__':
    test()
