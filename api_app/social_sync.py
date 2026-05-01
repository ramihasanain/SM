import requests
from django.utils import timezone
from .models import SocialProfile, Post, ScrapeJob

def fetch_facebook_posts(profile_id):
    """
    وظيفة مبدئية توضح كيفية سحب المنشورات والتعليقات من فيسبوك باستخدام الـ Access Token
    يمكن استدعاء هذه الوظيفة من خلال Celery أو Airflow لتعمل في الخلفية (Background Task).
    """
    try:
        profile = SocialProfile.objects.get(id=profile_id, platform='facebook')
    except SocialProfile.DoesNotExist:
        print("Profile not found")
        return

    access_token = profile.access_token
    if not access_token:
        print("No access token found for this profile")
        return

    # 1. إنشاء وظيفة السحب (Scrape Job) لتتبع العملية
    job = ScrapeJob.objects.create(
        profile=profile,
        status='running',
        started_at=timezone.now(),
        records_fetched=0
    )

    try:
        page_id = profile.platform_account_id
        page_token = profile.access_token
        page_name = profile.account_name or 'Unknown Page'
        print(f"Fetching posts for page: {page_name}...")

        records_fetched = 0

        graph_url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
        params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,shares,comments.summary(true).limit(100){id,message,created_time,from},reactions.summary(true).limit(100){name,type}',
            'limit': 20
        }
        
        response = requests.get(graph_url, params=params)
        data = response.json()
        
        if 'error' in data:
            print(f"Error fetching page {page_name}: {data['error']['message']}")
            job.status = 'failed'
            job.save()
            return

        posts_data = data.get('data', [])

        from .models import Reaction

        # 3. حفظ المنشورات في قاعدة البيانات
        for item in posts_data:
            message = item.get('message', '')
            if not message:
                continue # تخطي المنشورات بدون نص
                
            likes_count = item.get('reactions', {}).get('summary', {}).get('total_count', 0)
            comments_count = item.get('comments', {}).get('summary', {}).get('total_count', 0)
            shares_count = item.get('shares', {}).get('count', 0)
            created_time = item.get('created_time')
            
            parent_post, _ = Post.objects.update_or_create(
                raw_json={'facebook_id': item['id']},
                defaults={
                    'profile': profile,
                    'job': job,
                    'content': message,
                    'media_type': 'post',
                    'author_name': page_name,
                    'posted_at': created_time,
                    'engagement_json': {
                        'likes': likes_count,
                        'comments': comments_count,
                        'shares': shares_count
                    }
                }
            )
            records_fetched += 1
            
            # حفظ التفاعلات
            reactions_data = item.get('reactions', {}).get('data', [])
            for rxn in reactions_data:
                Reaction.objects.update_or_create(
                    post=parent_post,
                    author_name=rxn.get('name', 'مستخدم فيسبوك'),
                    defaults={'reaction_type': rxn.get('type', 'LIKE')}
                )

            # سحب التعليقات التابعة للمنشور وحفظها
            comments_data = item.get('comments', {}).get('data', [])
            for comment in comments_data:
                comment_msg = comment.get('message', '')
                if not comment_msg:
                    continue
                    
                comment_time = comment.get('created_time')
                Post.objects.update_or_create(
                    raw_json={'facebook_id': comment['id'], 'parent_post_id': item['id']},
                    defaults={
                        'profile': profile,
                        'job': job,
                        'content': comment_msg,
                        'media_type': 'comment',
                        'posted_at': comment_time,
                        'parent_post': parent_post,
                        'author_name': comment.get('from', {}).get('name', 'مستخدم فيسبوك'),
                        'engagement_json': {} 
                    }
                )
                records_fetched += 1
        
        # تحديث حالة الوظيفة بعد الانتهاء
        job.records_fetched = records_fetched
        job.status = 'completed'
        job.save()
        print(f"Successfully fetched {records_fetched} posts from Facebook.")

    except Exception as e:
        print(f"Sync failed: {str(e)}")
        job.status = 'failed'
        job.save()
