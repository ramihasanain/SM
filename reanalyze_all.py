import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import Post, SentimentResult, TopicTag
from api_app.sentiment_engine import bulk_analyze_posts

def run():
    print("=========================================")
    print("RE-ANALYZING ALL POSTS & COMMENTS FROM SCRATCH")
    print("=========================================")
    
    total_posts = Post.objects.count()
    print(f"Total posts and comments in database: {total_posts}")
    
    if total_posts == 0:
        print("❌ No posts found in database. Please scrape some data or run seed_db.py first!")
        return
        
    print("1. Clearing all old analysis results...")
    SentimentResult.objects.all().delete()
    TopicTag.objects.all().delete()
    print("   Cleared old SentimentResults and TopicTags successfully.")
    
    print("\n2. Running Hybrid Arabic Sentiment Engine on all posts...")
    all_posts = Post.objects.all()
    
    try:
        analyzed_count = bulk_analyze_posts(all_posts)
        print(f"\n3. SUCCESS: Re-analyzed {analyzed_count} posts and comments successfully!")
        print("   All results are now saved with Gemini 2.0 Flash / local fallback.")
    except Exception as e:
        print(f"\n❌ ERROR DURING BULK RE-ANALYSIS: {e}")
        import traceback
        traceback.print_exc()
        
    print("=========================================")

if __name__ == '__main__':
    run()
