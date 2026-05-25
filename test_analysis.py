import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import Post, SentimentResult
from api_app.sentiment_engine import bulk_analyze_posts

# Get all un-analyzed posts
pending = Post.objects.filter(sentiments__isnull=True)
print(f"Pending posts to analyze: {pending.count()}")

if pending.exists():
    try:
        analyzed = bulk_analyze_posts(pending)
        print(f"Successfully analyzed {analyzed} posts!")
    except Exception as e:
        print(f"Error during analysis: {e}")
else:
    print("No pending posts found.")
