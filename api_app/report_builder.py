"""Aggregate dashboard + sentiment data for PDF/Excel reports."""

from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .models import Post, ScrapeJob, SentimentResult, SocialProfile, TopicTag


def _apply_post_period(qs, period_from, period_to):
    if period_from:
        qs = qs.filter(posted_at__date__gte=period_from)
    if period_to:
        qs = qs.filter(posted_at__date__lte=period_to)
    return qs


def build_report_snapshot(user, period_from=None, period_to=None):
    posts_qs = Post.objects.filter(profile__user=user)
    posts_qs = _apply_post_period(posts_qs, period_from, period_to)

    total_posts_qs = posts_qs.filter(media_type='post')
    total_comments_qs = posts_qs.filter(media_type='comment')

    sentiments = SentimentResult.objects.filter(
        post__profile__user=user,
        post__media_type='comment',
        post__in=total_comments_qs,
    )
    total_sentiments = sentiments.count()
    pos_count = sentiments.filter(label='إيجابي').count()
    neg_count = sentiments.filter(label='سلبي').count()
    neu_count = sentiments.filter(label='محايد').count()
    denom = total_sentiments or 1

    csat = 0.0
    if total_sentiments:
        csat = round(((pos_count * 10) + (neu_count * 5)) / total_sentiments, 1)

    topics = TopicTag.objects.filter(
        result__post__profile__user=user,
        result__post__media_type='post',
        result__post__in=total_posts_qs,
    ).values('topic_label').annotate(count=Count('id')).order_by('-count')[:8]

    top_topics = []
    for t in topics:
        res = SentimentResult.objects.filter(
            tags__topic_label=t['topic_label'],
            post__profile__user=user,
            post__media_type='post',
            post__in=total_posts_qs,
        ).first()
        label = res.label if res else 'محايد'
        top_topics.append({
            'topic': t['topic_label'],
            'count': t['count'],
            'sentiment': label,
        })

    timeline = []
    engagement_timeline = []
    total_likes = total_shares = total_interactions = 0

    active_dates = set(
        total_posts_qs.filter(posted_at__isnull=False)
        .annotate(date=TruncDate('posted_at'))
        .values_list('date', flat=True)
        .distinct()
    ) | set(
        total_comments_qs.filter(posted_at__isnull=False)
        .annotate(date=TruncDate('posted_at'))
        .values_list('date', flat=True)
        .distinct()
    )
    active_dates.discard(None)

    if active_dates:
        start_date = min(active_dates)
        end_date = max(active_dates)

        posts_by_day = {
            row['date']: row['count']
            for row in total_posts_qs.filter(
                posted_at__date__gte=start_date,
                posted_at__date__lte=end_date,
            )
            .annotate(date=TruncDate('posted_at'))
            .values('date')
            .annotate(count=Count('id'))
            if row['date']
        }
        comments_by_day = {
            row['date']: row['count']
            for row in total_comments_qs.filter(
                posted_at__date__gte=start_date,
                posted_at__date__lte=end_date,
            )
            .annotate(date=TruncDate('posted_at'))
            .values('date')
            .annotate(count=Count('id'))
            if row['date']
        }
        sentiment_by_day = {
            row['date']: row
            for row in sentiments.filter(
                post__posted_at__date__gte=start_date,
                post__posted_at__date__lte=end_date,
            )
            .annotate(date=TruncDate('post__posted_at'))
            .values('date')
            .annotate(
                pos=Count('id', filter=Q(label='إيجابي')),
                neg=Count('id', filter=Q(label='سلبي')),
                neu=Count('id', filter=Q(label='محايد')),
            )
            if row['date']
        }

        day = start_date
        while day <= end_date:
            sent = sentiment_by_day.get(day, {})
            posts_n = posts_by_day.get(day, 0)
            comments_n = comments_by_day.get(day, 0)
            pos_n = sent.get('pos', 0)
            neg_n = sent.get('neg', 0)
            neu_n = sent.get('neu', 0)
            if posts_n or comments_n or pos_n or neg_n or neu_n:
                timeline.append({
                    'date': day.strftime('%Y-%m-%d'),
                    'posts': posts_n,
                    'comments': comments_n,
                    'pos': pos_n,
                    'neg': neg_n,
                    'neu': neu_n,
                })
            day += timedelta(days=1)

    engagement_buckets = {}
    for post in total_posts_qs.filter(posted_at__isnull=False).iterator():
        eg = post.engagement_json or {}
        likes_n = int(eg.get('likes') or 0)
        shares_n = int(eg.get('shares') or 0)
        comments_eng = int(eg.get('comments') or 0)
        if not (likes_n or shares_n or comments_eng):
            continue
        day = post.posted_at.date()
        if day not in engagement_buckets:
            engagement_buckets[day] = {'likes': 0, 'shares': 0, 'comments_eng': 0}
        engagement_buckets[day]['likes'] += likes_n
        engagement_buckets[day]['shares'] += shares_n
        engagement_buckets[day]['comments_eng'] += comments_eng

    for day in sorted(engagement_buckets.keys()):
        bucket = engagement_buckets[day]
        interactions_n = bucket['likes'] + bucket['shares'] + bucket['comments_eng']
        total_likes += bucket['likes']
        total_shares += bucket['shares']
        total_interactions += interactions_n
        engagement_timeline.append({
            'date': day.strftime('%Y-%m-%d'),
            'likes': bucket['likes'],
            'shares': bucket['shares'],
            'interactions': interactions_n,
        })

    return {
        'period_from': period_from.isoformat() if period_from else None,
        'period_to': period_to.isoformat() if period_to else None,
        'total_posts': total_posts_qs.count(),
        'total_comments': total_comments_qs.count(),
        'linked_accounts': SocialProfile.objects.filter(user=user).count(),
        'completed_scrapes': ScrapeJob.objects.filter(profile__user=user, status='completed').count(),
        'sentiment_summary': {
            'pos_pct': round((pos_count / denom) * 100, 1),
            'neg_pct': round((neg_count / denom) * 100, 1),
            'neu_pct': round((neu_count / denom) * 100, 1),
            'pos_count': pos_count,
            'neg_count': neg_count,
            'neu_count': neu_count,
            'csat': csat,
        },
        'top_topics': top_topics,
        'timeline': timeline,
        'engagement_timeline': engagement_timeline,
        'engagement_summary': {
            'likes': total_likes,
            'shares': total_shares,
            'interactions': total_interactions,
        },
    }
