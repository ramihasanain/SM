import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import (
    CustomUser, SocialProfile, ScrapeJob, Post, 
    AIModel, AnalysisBatch, SentimentResult, TopicTag
)

def run():
    print("Clearing old data...")
    SentimentResult.objects.all().delete()
    TopicTag.objects.all().delete()
    Post.objects.all().delete()
    ScrapeJob.objects.all().delete()
    SocialProfile.objects.all().delete()
    AnalysisBatch.objects.all().delete()
    AIModel.objects.all().delete()

    user = CustomUser.objects.first()
    if not user:
        user = CustomUser.objects.create_superuser('admin', 'admin@example.com', 'admin')

    # Create AI Model
    ai_model = AIModel.objects.create(
        model_name="Llama-3-Arabic",
        version="v1.0",
        lang="ar",
        provider="Meta",
        is_active=True
    )

    # Create Profiles
    fb_profile = SocialProfile.objects.create(user=user, platform='facebook', url="https://facebook.com/page")
    x_profile = SocialProfile.objects.create(user=user, platform='twitter', url="https://twitter.com/page")

    # Create Scrape Jobs
    now = timezone.now()
    job_fb = ScrapeJob.objects.create(profile=fb_profile, status='completed', started_at=now - timedelta(days=1), records_fetched=100)
    job_x = ScrapeJob.objects.create(profile=x_profile, status='completed', started_at=now - timedelta(days=1), records_fetched=100)

    # Create Batch
    batch = AnalysisBatch.objects.create(user=user, trigger_type='manual', status='completed', posts_analyzed=200)

    topics = ['خدمة العملاء', 'جودة المنتج', 'سرعة التوصيل', 'العروض والخصومات', 'تجربة الموقع', 'التغليف', 'سياسة الإرجاع', 'طرق الدفع']
    sentiments = ['إيجابي', 'سلبي', 'محايد']

    sample_contents = [
        "منتج ممتاز جداً وتغليف رائع، شكراً لكم!",
        "تجربتي كانت سيئة مع خدمة العملاء للأسف.",
        "تم استلام الطلب في الموعد المحدد.",
        "هل يوجد خصم على هذا المنتج؟",
        "جودة الخامات ممتازة وتستحق السعر.",
        "تأخير غير طبيعي في التوصيل، لن أتعامل معكم مرة أخرى.",
        "الموقع سهل الاستخدام وتجربة الشراء ممتعة.",
        "سياسة الإرجاع معقدة بعض الشيء."
    ]

    print("Creating posts...")
    for i in range(200):
        is_fb = random.choice([True, False])
        profile = fb_profile if is_fb else x_profile
        job = job_fb if is_fb else job_x

        content = random.choice(sample_contents)
        # Randomize posted_at within last 30 days
        posted_at = now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        
        post = Post.objects.create(
            profile=profile,
            job=job,
            content=f"{content} - {i}",
            detected_lang='ar',
            posted_at=posted_at,
            media_type='منشور',
            engagement_json={
                "likes": random.randint(0, 500),
                "shares": random.randint(0, 50)
            }
        )

        label = random.choices(['إيجابي', 'سلبي', 'محايد'], weights=[60, 20, 20])[0]
        pos_score, neg_score, neu_score = 0, 0, 0
        if label == 'إيجابي':
            pos_score = random.uniform(0.7, 0.99)
            neg_score = random.uniform(0, 0.1)
            neu_score = 1.0 - pos_score - neg_score
        elif label == 'سلبي':
            neg_score = random.uniform(0.7, 0.99)
            pos_score = random.uniform(0, 0.1)
            neu_score = 1.0 - pos_score - neg_score
        else:
            neu_score = random.uniform(0.7, 0.99)
            pos_score = random.uniform(0, 0.15)
            neg_score = 1.0 - pos_score - neu_score

        result = SentimentResult.objects.create(
            post=post,
            model=ai_model,
            batch=batch,
            label=label,
            pos_score=pos_score,
            neg_score=neg_score,
            neu_score=neu_score,
            lang_processed='ar'
        )

        topic = random.choice(topics)
        TopicTag.objects.create(
            result=result,
            topic_label=topic,
            confidence=random.uniform(0.6, 0.99)
        )

    print("Successfully seeded 200 posts with sentiments and topics.")

if __name__ == '__main__':
    run()
