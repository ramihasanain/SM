import logging
import requests
from django.utils import timezone
from .models import SocialProfile, Post, ScrapeJob, Reaction

logger = logging.getLogger(__name__)


def refresh_facebook_page_meta(profile):
    """تحديث صورة الصفحة وعدد المتابعين من Graph API."""
    if profile.platform != 'facebook' or not profile.access_token or not profile.platform_account_id:
        return
    try:
        page_info_url = f"https://graph.facebook.com/v19.0/{profile.platform_account_id}"
        page_info_params = {
            'access_token': profile.access_token,
            'fields': 'picture.type(large),followers_count',
        }
        info_res = requests.get(page_info_url, params=page_info_params, timeout=15).json()
        if 'error' in info_res:
            return
        pic_url = info_res.get('picture', {}).get('data', {}).get('url', '')
        followers = info_res.get('followers_count', profile.followers_count)
        update_fields = []
        if pic_url:
            profile.profile_picture_url = pic_url
            update_fields.append('profile_picture_url')
        if followers is not None:
            profile.followers_count = followers
            update_fields.append('followers_count')
        if update_fields:
            profile.save(update_fields=update_fields)
    except Exception:
        logger.exception('Could not refresh page meta for profile %s', profile.id)


def fetch_facebook_posts(profile_id):
    """سحب المنشورات والتعليقات من فيسبوك باستخدام Access Token الصفحة."""
    try:
        profile = SocialProfile.objects.get(id=profile_id, platform='facebook')
    except SocialProfile.DoesNotExist:
        logger.warning('Facebook profile not found: %s', profile_id)
        return

    access_token = profile.access_token
    if not access_token:
        logger.warning('No access token for profile %s', profile_id)
        return

    refresh_facebook_page_meta(profile)

    job = ScrapeJob.objects.create(
        profile=profile,
        status='running',
        started_at=timezone.now(),
        records_fetched=0,
    )

    try:
        page_id = profile.platform_account_id
        page_token = profile.access_token
        page_name = profile.account_name or 'Unknown Page'
        logger.info('Fetching posts for page: %s', page_name)

        records_fetched = 0
        graph_url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
        params = {
            'access_token': page_token,
            'fields': 'id,message,created_time,shares,comments.summary(true).limit(100){id,message,created_time,from},reactions.summary(true).limit(100){name,type}',
            'limit': 20,
        }

        response = requests.get(graph_url, params=params, timeout=60)
        data = response.json()

        if 'error' in data:
            logger.error('Facebook API error for %s: %s', page_name, data['error'].get('message'))
            job.status = 'failed'
            job.save(update_fields=['status'])
            return

        posts_data = data.get('data', [])

        for item in posts_data:
            message = item.get('message', '')
            if not message:
                continue

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
                        'shares': shares_count,
                    },
                },
            )
            records_fetched += 1

            for rxn in item.get('reactions', {}).get('data', []):
                Reaction.objects.update_or_create(
                    post=parent_post,
                    author_name=rxn.get('name', 'مستخدم فيسبوك'),
                    defaults={'reaction_type': rxn.get('type', 'LIKE')},
                )

            for comment in item.get('comments', {}).get('data', []):
                comment_msg = comment.get('message', '')
                if not comment_msg:
                    continue

                Post.objects.update_or_create(
                    raw_json={'facebook_id': comment['id'], 'parent_post_id': item['id']},
                    defaults={
                        'profile': profile,
                        'job': job,
                        'content': comment_msg,
                        'media_type': 'comment',
                        'posted_at': comment.get('created_time'),
                        'parent_post': parent_post,
                        'author_name': comment.get('from', {}).get('name', 'مستخدم فيسبوك'),
                        'engagement_json': {},
                    },
                )
                records_fetched += 1

        job.records_fetched = records_fetched
        job.status = 'completed'
        job.save(update_fields=['records_fetched', 'status'])
        logger.info('Fetched %s records from Facebook for %s', records_fetched, page_name)

    except Exception:
        logger.exception('Facebook sync failed for profile %s', profile_id)
        job.status = 'failed'
        job.save(update_fields=['status'])
