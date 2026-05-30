import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.sentiment_engine import analyze_sentiment_local, analyze_text_hybrid

CASES = [
    "اية الرزق . الله يفتحها عليكم",
    "مطبخ ست الحبايب أكل بيتي سدر منسف على كيلو لحم روماني 15 دينار",
    "كم سعر الشيشبرك والكبة المشوية",
    "موجود كبة مشوية وكم سعرها",
    "كيف الاسعار ممكن نعرف",
    "Ghada Issa برمضان ع أكلة منهم اوك",
    "عملائنا الكرام كل عام وانتم بخير. اللي حاب يطلب مني شي يرسلي الان على رقم",
]

for text in CASES:
    local = analyze_sentiment_local(text)
    hybrid = analyze_text_hybrid(text)
    print("=" * 60)
    print(text[:70])
    print(f"LOCAL  -> {local['sentiment']} | sarc={local['is_sarcastic']} | {local['engine_used']}")
    if local.get('sarcasm_explanation'):
        print(f"         {local['sarcasm_explanation']}")
    print(f"HYBRID -> {hybrid['sentiment']} | sarc={hybrid['is_sarcastic']} | {hybrid['engine_used']}")
    if hybrid.get('sarcasm_explanation'):
        print(f"         {hybrid['sarcasm_explanation']}")
