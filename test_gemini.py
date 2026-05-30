import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.sentiment_engine import (
    analyze_text_hybrid,
    analyze_sentiment_local,
    _validate_sarcasm_result,
    HAS_GEMINI_SDK,
)


LOCAL_SARCASM_CASES = [
    {
        "text": "ممتاز لدرجة ما بشتغل",
        "expect_sarcastic": True,
        "expect_sentiment": "سلبي",
        "label": "hyperbolic degree + negation",
    },
    {
        "text": "الخدمة جيدة لكن السعر غالي",
        "expect_sarcastic": False,
        "expect_sentiment": None,
        "label": "mixed honest review",
    },
    {
        "text": "ما رضيت عن المنتج ابداً",
        "expect_sarcastic": False,
        "expect_sentiment": None,
        "label": "direct complaint",
    },
    {
        "text": "سريع بس ما بفتح",
        "expect_sarcastic": False,
        "expect_sentiment": None,
        "label": "but-clause complaint (not sarcasm)",
    },
    {
        "text": "اللابتوب شغال دفّاية بالصيف! 🔥",
        "expect_sarcastic": True,
        "expect_sentiment": "سلبي",
        "label": "praise + emoji + negative context",
    },
    {
        "text": "الخدمة سريعة لدرجة إنها ما بتفتح!",
        "expect_sarcastic": True,
        "expect_sentiment": "سلبي",
        "label": "speed praise + degree + negation",
    },
]


def run_local_sarcasm_tests():
    print("\n--- Local Lexicon Sarcasm Tests (Conservative Rules) ---")
    passed = 0
    failed = 0

    for case in LOCAL_SARCASM_CASES:
        res = analyze_sentiment_local(case["text"])
        ok = res.get("is_sarcastic") == case["expect_sarcastic"]
        if case["expect_sentiment"]:
            ok = ok and res.get("sentiment") == case["expect_sentiment"]

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        print(f"  [{status}] {case['label']}")
        print(f"         text: {case['text']}")
        print(f"         sentiment={res.get('sentiment')}, is_sarcastic={res.get('is_sarcastic')}")
        if not ok:
            print(f"         expected sarcastic={case['expect_sarcastic']}, sentiment={case.get('expect_sentiment')}")

    print(f"\n  Local tests: {passed} passed, {failed} failed")
    return failed == 0


def run_validation_tests():
    print("\n--- Gemini Post-Validation Tests ---")
    passed = 0
    failed = 0

    cases = [
        (
            "ما رضيت عن المنتج",
            {"is_sarcastic": True, "final_sentiment": "سلبي", "sarcasm_explanation": "تهكم"},
            False,
            "plain negative should not stay sarcastic",
        ),
        (
            "ممتاز لدرجة ما بشتغل",
            {"is_sarcastic": True, "final_sentiment": "سلبي", "sarcasm_explanation": "مديح ساخر"},
            True,
            "clear sarcasm with explanation kept",
        ),
        (
            "شيء ما",
            {"is_sarcastic": True, "final_sentiment": "سلبي", "sarcasm_explanation": ""},
            False,
            "empty explanation rejects sarcasm",
        ),
    ]

    for text, data, expect_sarcastic, label in cases:
        result = _validate_sarcasm_result(text, dict(data))
        ok = result.get("is_sarcastic") == expect_sarcastic
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {label}: is_sarcastic={result.get('is_sarcastic')}")

    print(f"\n  Validation tests: {passed} passed, {failed} failed")
    return failed == 0


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

    local_ok = run_local_sarcasm_tests()
    validation_ok = run_validation_tests()

    test_comment = "اللابتوب شغال دفّاية بالصيف! 🔥"
    parent_post = "اشتريت هذا اللابتوب الجديد اليوم"
    print(f"\n3. Testing sarcastic comment (hybrid): '{test_comment}'")
    print(f"   Parent Post: '{parent_post}'")

    hybrid_ok = True
    try:
        res = analyze_text_hybrid(test_comment, parent_text=parent_post)
        print("\n4. COMMENT ANALYSIS RESULT (Hybrid):")
        print(f"   Sentiment: {res.get('sentiment')}")
        print(f"   Engine Used: {res.get('engine_used')}")
        print(f"   Is Sarcastic: {res.get('is_sarcastic')}")
        print(f"   Sarcasm Explanation: {res.get('sarcasm_explanation')}")
        print(f"   Topic: {res.get('topic')}")
        print(f"   Confidence: {res.get('confidence')}")
        print(f"   Keywords: {res.get('keywords')}")
    except Exception as e:
        hybrid_ok = False
        print(f"\nRUNTIME ERROR DURING COMMENT ANALYSIS: {e}")
        import traceback
        traceback.print_exc()

    test_post = "الخدمة سريعة لدرجة إنها ما بتفتح!"
    print(f"\n=========================================")
    print(f"5. Testing main post: '{test_post}'")

    try:
        res = analyze_text_hybrid(test_post)
        print("\n6. MAIN POST ANALYSIS RESULT (Hybrid):")
        print(f"   Sentiment: {res.get('sentiment')}")
        print(f"   Engine Used: {res.get('engine_used')}")
        print(f"   Is Sarcastic: {res.get('is_sarcastic')}")
        print(f"   Topic: {res.get('topic')}")
        print(f"   Confidence: {res.get('confidence')}")
        print(f"   Keywords: {res.get('keywords')}")
    except Exception as e:
        print(f"\nRUNTIME ERROR DURING POST ANALYSIS: {e}")

    print("=========================================")
    all_ok = local_ok and validation_ok and hybrid_ok
    print(f"OVERALL: {'ALL TESTS PASSED' if all_ok else 'SOME TESTS FAILED'}")
    print("=========================================")


if __name__ == '__main__':
    test()
