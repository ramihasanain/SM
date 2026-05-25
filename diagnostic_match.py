import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import Post, SentimentResult, TopicTag

posts = Post.objects.filter(media_type='post')
print(f"Total parent posts: {posts.count()}")
for p in posts:
    sent = p.sentiments.first()
    tag = sent.tags.first() if sent else None
    print(f"Post ID: {p.id} | Content snippet: '{p.content[:30]}' | Sentiment: {sent.label if sent else 'None'} | Engine: {sent.engine_used if sent else 'None'} | Topic: {tag.topic_label if tag else 'None'}")
