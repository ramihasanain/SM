import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api_app.models import Post, TopicTag
from api_app.sentiment_engine import batch_ai_topic_modeling

def reclassify():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("ai_key")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in environment variables!")
        return
        
    posts = Post.objects.filter(media_type='post')
    count = posts.count()
    print(f"🔄 Starting Batch AI Topic Modeling for all {count} parent posts...")
    
    posts_data = [{"id": p.id, "content": p.content[:400]} for p in posts]
    
    try:
        batch_results = batch_ai_topic_modeling(posts_data, api_key)
        results_map = {item["id"]: item for item in batch_results if "id" in item}
        
        updated_count = 0
        for post in posts:
            ai_res = results_map.get(post.id)
            if ai_res:
                ai_topic = ai_res.get("topic", "عام")
                sent_res = post.sentiments.first()
                if sent_res:
                    tag = sent_res.tags.first()
                    if tag:
                        tag.topic_label = ai_topic
                        tag.save()
                        print(f"   ✅ Updated Post ID {post.id} topic to: '{ai_topic}'")
                        updated_count += 1
                        
        print(f"\n🎉 Reclassification fully complete! Updated {updated_count} posts successfully.")
    except Exception as e:
        print(f"❌ Error during batch reclassification: {e}")

if __name__ == '__main__':
    reclassify()
