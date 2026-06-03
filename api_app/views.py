import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post, Reaction,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification,
)
from .serializers import (
    CustomUserSerializer, SocialProfileSerializer, PaymentTxnSerializer, ScrapeJobSerializer, PostSerializer,
    PlatformMetaSerializer, AnalysisBatchSerializer, AIModelSerializer, SentimentResultSerializer,
    TopicTagSerializer, ReportSerializer, NotificationSerializer,
)

from django.conf import settings

# ==========================================================
# 1. USER VIEWS
@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_me(request):
    if request.method == 'GET':
        serializer = CustomUserSerializer(request.user)
        return Response(serializer.data)
    elif request.method in ['PUT', 'PATCH']:
        serializer = CustomUserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def user_list_create(request):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        users = CustomUser.objects.all()
        serializer = CustomUserSerializer(users, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, pk):
    try:
        user = CustomUser.objects.get(pk=pk)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = CustomUserSerializer(user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 2. SOCIAL PROFILE VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def profile_list_create(request):
    if request.method == 'GET':
        from .social_sync import refresh_facebook_page_meta
        items = SocialProfile.objects.filter(user=request.user)
        for profile in items:
            if profile.platform == 'facebook' and profile.access_token and not profile.profile_picture_url:
                refresh_facebook_page_meta(profile)
        serializer = SocialProfileSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = SocialProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def profile_detail(request, pk):
    try:
        item = SocialProfile.objects.get(pk=pk)
    except SocialProfile.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SocialProfileSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = SocialProfileSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ==========================================================
# 3. PAYMENT TXN VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def payment_txn_list_create(request):
    if request.method == 'GET':
        items = PaymentTxn.objects.filter(user=request.user)
        serializer = PaymentTxnSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        # Attach the current user to the data
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = PaymentTxnSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def payment_txn_detail(request, pk):
    try:
        item = PaymentTxn.objects.get(pk=pk)
    except PaymentTxn.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PaymentTxnSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = PaymentTxnSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 4. SCRAPE JOB VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def scrape_job_list_create(request):
    if request.method == 'GET':
        items = ScrapeJob.objects.filter(profile__user=request.user)
        serializer = ScrapeJobSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ScrapeJobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def scrape_job_detail(request, pk):
    try:
        item = ScrapeJob.objects.get(pk=pk, profile__user=request.user)
    except ScrapeJob.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ScrapeJobSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ScrapeJobSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 5. POST VIEWS
# ==========================================================
import threading

def trigger_background_analysis(posts_qs):
    # Only select posts that do not have any SentimentResult yet
    pending_posts = posts_qs.filter(sentiments__isnull=True)
    if not pending_posts.exists():
        return
        
    post_ids = list(pending_posts.values_list('id', flat=True))
    
    def bg_task():
        from django.db import connection
        connection.close() # Prevent database session locking
        
        from .sentiment_engine import bulk_analyze_posts
        
        thread_posts = Post.objects.filter(id__in=post_ids)
        try:
            bulk_analyze_posts(thread_posts)
        except Exception:
            logging.getLogger(__name__).exception('Background analysis failed')
            
    thread = threading.Thread(target=bg_task)
    thread.daemon = True
    thread.start()

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def post_list_create(request):
    if request.method == 'GET':
        items = Post.objects.filter(profile__user=request.user)\
            .select_related('profile')\
            .prefetch_related('sentiments', 'sentiments__tags')
            
        # Automatically trigger background analysis for any pending posts
        trigger_background_analysis(items)
        
        profile_id = request.query_params.get('profile_id')
        if profile_id:
            items = items.filter(profile_id=profile_id)
        serializer = PostSerializer(items.order_by('-posted_at'), many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def post_detail(request, pk):
    try:
        item = Post.objects.get(pk=pk, profile__user=request.user)
    except Post.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PostSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = PostSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 6. PLATFORM META VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def platform_meta_list_create(request):
    if request.method == 'GET':
        items = PlatformMeta.objects.filter(post__profile__user=request.user)
        serializer = PlatformMetaSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PlatformMetaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def platform_meta_detail(request, pk):
    try:
        item = PlatformMeta.objects.get(pk=pk, post__profile__user=request.user)
    except PlatformMeta.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = PlatformMetaSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = PlatformMetaSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 7. ANALYSIS BATCH VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def analysis_batch_list_create(request):
    if request.method == 'GET':
        items = AnalysisBatch.objects.filter(user=request.user)
        serializer = AnalysisBatchSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AnalysisBatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def analysis_batch_detail(request, pk):
    try:
        item = AnalysisBatch.objects.get(pk=pk, user=request.user)
    except AnalysisBatch.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AnalysisBatchSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = AnalysisBatchSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 8. AI MODEL VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
def ai_model_list_create(request):
    if request.method == 'GET':
        items = AIModel.objects.all()
        serializer = AIModelSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AIModelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def ai_model_detail(request, pk):
    try:
        item = AIModel.objects.get(pk=pk)
    except AIModel.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AIModelSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = AIModelSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 9. SENTIMENT RESULT VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def sentiment_result_list_create(request):
    if request.method == 'GET':
        items = SentimentResult.objects.filter(post__profile__user=request.user)
        serializer = SentimentResultSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = SentimentResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def sentiment_result_detail(request, pk):
    try:
        item = SentimentResult.objects.get(pk=pk, post__profile__user=request.user)
    except SentimentResult.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = SentimentResultSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = SentimentResultSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 10. TOPIC TAG VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def topic_tag_list_create(request):
    if request.method == 'GET':
        items = TopicTag.objects.filter(result__post__profile__user=request.user)
        serializer = TopicTagSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = TopicTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def topic_tag_detail(request, pk):
    try:
        item = TopicTag.objects.get(pk=pk, result__post__profile__user=request.user)
    except TopicTag.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TopicTagSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = TopicTagSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ==========================================================
# 11. REPORT VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def report_list_create(request):
    if request.method == 'GET':
        items = Report.objects.filter(user=request.user)
        serializer = ReportSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = ReportSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def report_detail(request, pk):
    try:
        item = Report.objects.get(pk=pk, user=request.user)
    except Report.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ReportSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ReportSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_excel_report(request, pk):
    from django.http import HttpResponse
    import csv

    try:
        report = Report.objects.get(pk=pk, user=request.user)
    except Report.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    posts = Post.objects.filter(profile__user=request.user)
    if report.period_from:
        posts = posts.filter(posted_at__date__gte=report.period_from)
    if report.period_to:
        posts = posts.filter(posted_at__date__lte=report.period_to)

    # Set up HTTP response with UTF-8 BOM to ensure Excel opens Arabic correctly
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="report_{report.id}.csv"'
    
    # Write UTF-8 BOM bytes so Excel automatically reads it as UTF-8
    response.write(b'\xef\xbb\xbf')

    writer = csv.writer(response)
    # Write header
    writer.writerow([
        'معرف المنشور (ID)', 
        'المحتوى (Content)', 
        'تاريخ النشر (Posted At)', 
        'المشاعر (Sentiment)', 
        'الموضوع (Topic)', 
        'المحرك المستخدم (Engine)', 
        'هل يحتوي على سخرية؟ (Is Sarcastic)', 
        'تفسير السخرية (Sarcasm Explanation)'
    ])

    for post in posts:
        # Get first sentiment result
        sentiment_res = post.sentiments.first()
        sentiment_label = sentiment_res.label if sentiment_res else 'محايد'
        engine = sentiment_res.engine_used if sentiment_res else 'Local Lexicon'
        is_sarcastic = 'نعم' if (sentiment_res and sentiment_res.is_sarcastic) else 'لا'
        sarcasm_explanation = sentiment_res.sarcasm_explanation if sentiment_res else ''
        
        # Get topic tag
        topic_tag = sentiment_res.tags.first() if sentiment_res else None
        topic = topic_tag.topic_label if topic_tag else 'غير محدد'

        writer.writerow([
            post.id,
            post.content,
            post.posted_at.strftime('%Y-%m-%d %H:%M:%S') if post.posted_at else '',
            sentiment_label,
            topic,
            engine,
            is_sarcastic,
            sarcasm_explanation
        ])

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_pdf_report(request, pk):
    from django.http import HttpResponse
    from .report_builder import build_report_snapshot
    from .report_pdf import build_report_pdf

    try:
        report = Report.objects.get(pk=pk, user=request.user)
    except Report.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    lang = request.query_params.get('lang', 'ar')
    if lang not in ('ar', 'en'):
        lang = 'ar'

    snapshot = build_report_snapshot(request.user, report.period_from, report.period_to)
    title = f"Analytica Report #{report.id}"
    if lang == 'ar':
        title = f"تقرير Analytica #{report.id}"

    pdf_bytes = build_report_pdf(snapshot, lang=lang, report_title=title)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{report.id}.pdf"'
    return response


# ==========================================================
# 12. NOTIFICATION VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def notification_list_create(request):
    if request.method == 'GET':
        items = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def notification_detail(request, pk):
    try:
        item = Notification.objects.get(pk=pk, user=request.user)
    except Notification.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = NotificationSerializer(item)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = NotificationSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.method == 'DELETE':
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# ==========================================================
# 13. DASHBOARD STATS
# ==========================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    posts_qs = Post.objects.filter(profile__user=request.user)
    total_posts_qs = posts_qs.filter(media_type='post')
    total_comments_qs = posts_qs.filter(media_type='comment')
    
    total_posts = total_posts_qs.count()
    total_comments = total_comments_qs.count()
    
    linked_accounts = SocialProfile.objects.filter(user=request.user).count()
    completed_scrapes = ScrapeJob.objects.filter(profile__user=request.user, status='completed').count()
    
    sentiments = SentimentResult.objects.filter(post__profile__user=request.user, post__media_type='comment')
    total_sentiments = sentiments.count() or 1
    pos_count = sentiments.filter(label='إيجابي').count()
    neg_count = sentiments.filter(label='سلبي').count()
    neu_count = sentiments.filter(label='محايد').count()
    
    topics = TopicTag.objects.filter(
        result__post__profile__user=request.user,
        result__post__media_type='post'
    ).values('topic_label').annotate(count=Count('id')).order_by('-count')[:5]
    top_topics = []
    for t in topics:
        res = SentimentResult.objects.filter(
            tags__topic_label=t['topic_label'],
            post__profile__user=request.user,
            post__media_type='post'
        ).first()
        label = res.label if res else 'محايد'
        top_topics.append({
            'topic': t['topic_label'],
            'count': t['count'],
            'sentiment': label,
            'badge': 'badge-green' if label == 'إيجابي' else 'badge-red' if label == 'سلبي' else 'badge-amber'
        })
        
    fb_posts = total_posts_qs.filter(profile__platform='facebook').count()
    
    # Timeline: only from first to last day that has posts, comments, or sentiment data
    from django.db.models.functions import TruncDate
    from django.db.models import Q

    def _distinct_posted_dates(qs):
        return set(
            qs.filter(posted_at__isnull=False)
            .annotate(date=TruncDate('posted_at'))
            .values_list('date', flat=True)
            .distinct()
        )

    active_dates = (
        _distinct_posted_dates(posts_qs.filter(media_type='post'))
        | _distinct_posted_dates(posts_qs.filter(media_type='comment'))
        | set(
            SentimentResult.objects.filter(
                post__profile__user=request.user,
                post__media_type='comment',
                post__posted_at__isnull=False,
            )
            .annotate(date=TruncDate('post__posted_at'))
            .values_list('date', flat=True)
            .distinct()
        )
    )
    active_dates.discard(None)

    timeline = []
    if active_dates:
        start_date = min(active_dates)
        end_date = max(active_dates)

        posts_by_day = {
            row['date']: row['count']
            for row in posts_qs.filter(
                media_type='post',
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
            for row in posts_qs.filter(
                media_type='comment',
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
            for row in SentimentResult.objects.filter(
                post__profile__user=request.user,
                post__media_type='comment',
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
        idx = 0
        while day <= end_date:
            sent = sentiment_by_day.get(day, {})
            posts_n = posts_by_day.get(day, 0)
            comments_n = comments_by_day.get(day, 0)
            pos_n = sent.get('pos', 0)
            neg_n = sent.get('neg', 0)
            neu_n = sent.get('neu', 0)
            if posts_n or comments_n or pos_n or neg_n or neu_n:
                timeline.append({
                    'day': idx + 1,
                    'date': day.strftime('%Y-%m-%d'),
                    'posts': posts_n,
                    'comments': comments_n,
                    'pos': pos_n,
                    'neg': neg_n,
                    'neu': neu_n,
                })
                idx += 1
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

    engagement_timeline = []
    total_likes = total_shares = total_interactions = 0
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

    return Response({
        'total_posts': total_posts,
        'total_comments': total_comments,
        'linked_accounts': linked_accounts,
        'completed_scrapes': completed_scrapes,
        'sentiment_summary': {
            'pos_pct': round((pos_count / total_sentiments) * 100, 1),
            'neg_pct': round((neg_count / total_sentiments) * 100, 1),
            'neu_pct': round((neu_count / total_sentiments) * 100, 1),
            'pos_count': pos_count,
            'neg_count': neg_count,
            'neu_count': neu_count,
        },
        'platform_distribution': {
            'facebook': fb_posts,
        },
        'top_topics': top_topics,
        'timeline': timeline,
        'engagement_timeline': engagement_timeline,
        'engagement_summary': {
            'likes': total_likes,
            'shares': total_shares,
            'interactions': total_interactions,
        },
    })

from .social_sync import fetch_facebook_posts

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_profile(request, pk):
    try:
        profile = SocialProfile.objects.get(pk=pk, user=request.user)
    except SocialProfile.DoesNotExist:
        return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
    if profile.platform == 'facebook':
        try:
            fetch_facebook_posts(profile.id)
            profile.refresh_from_db()
            
            # Asynchronous automatic sentiment analysis trigger after sync
            un_analyzed = Post.objects.filter(profile=profile, sentiments__isnull=True)
            trigger_background_analysis(un_analyzed)
            
            return Response({'message': 'Synced successfully', 'profile': SocialProfileSerializer(profile).data})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Sync is only supported for Facebook pages'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_pending_posts(request):
    """
    يقوم بتحليل المشاعر لجميع المنشورات المعلقة التي لم يتم تحليلها بعد للمستخدم الحالي.
    """
    from .sentiment_engine import bulk_analyze_posts
    
    # Get all un-analyzed posts for this user
    pending_posts = Post.objects.filter(profile__user=request.user, sentiments__isnull=True)
    count = pending_posts.count()
    
    if count == 0:
        return Response({
            'message': 'لا توجد منشورات معلقة بحاجة للتحليل.',
            'analyzed_count': 0
        })
        
    # Create Analysis Batch record
    batch = AnalysisBatch.objects.create(
        user=request.user,
        trigger_type='manual',
        status='running',
        posts_analyzed=0
    )
    
    try:
        analyzed_count = bulk_analyze_posts(pending_posts, batch=batch)
        batch.posts_analyzed = analyzed_count
        batch.status = 'completed'
        batch.save()
        
        return Response({
            'message': f'تم تحليل {analyzed_count} منشوراً بنجاح باستخدام المعمارية الهجينة!',
            'analyzed_count': analyzed_count,
            'batch_id': batch.id
        })
    except Exception as e:
        batch.status = 'failed'
        batch.save()
        return Response({
            'error': f'فشل في تحليل المنشورات: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def post_details(request, pk):
    try:
        post = Post.objects.prefetch_related('sentiments', 'sentiments__tags').get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
    post_data = PostSerializer(post).data
    
    reactions = Reaction.objects.filter(post=post)
    reactions_list = [{'id': r.id, 'author_name': r.author_name, 'reaction_type': r.reaction_type} for r in reactions]
    
    comments = Post.objects.filter(parent_post=post, media_type='comment')\
        .select_related('profile')\
        .prefetch_related('sentiments', 'sentiments__tags')
    comments_list = []
    for c in comments:
        c_data = PostSerializer(c).data
        comments_list.append({
            'id': c.id,
            'content': c.content,
            'author_name': c.author_name,
            'sentiment': c_data.get('sentiment', 'محايد'),
            'score': c_data.get('score', 0.5),
            'topic': '',
            # Include new sarcasm and engine details in nested views
            'is_sarcastic': c_data.get('is_sarcastic', False),
            'sarcasm_explanation': c_data.get('sarcasm_explanation', ''),
            'engine_used': c_data.get('engine_used', 'Local Lexicon'),
            'is_analyzed': c_data.get('is_analyzed', False)
        })
        
    return Response({
        'post': post_data,
        'reactions': reactions_list,
        'comments': comments_list
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_topics(request):
    """
    يجلب جميع المواضيع التصنيفية الفريدة الموجودة في قاعدة البيانات للمنشورات الأصلية للمستخدم الحالي.
    """
    labels = TopicTag.objects.filter(
        result__post__profile__user=request.user,
        result__post__media_type='post'
    ).values_list('topic_label', flat=True).distinct()
    
    unique_topics = sorted(list(set([l for l in labels if l and l.strip()])))
    if not unique_topics:
        unique_topics = ['عام']
        
    return Response(unique_topics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def analysis_operations_log(request):
    """
    يعود بسجل تفصيلي لجميع عمليات التحليل ومحركات التصنيف المستخدمة للمنشورات والتعليقات.
    """
    posts = Post.objects.filter(profile__user=request.user)\
        .select_related('profile')\
        .prefetch_related('sentiments', 'sentiments__tags')\
        .order_by('-posted_at')
        
    log_data = []
    for p in posts:
        sentiment = p.sentiments.first()
        tag = sentiment.tags.first() if sentiment else None
        
        log_data.append({
            'id': p.id,
            'content': p.content[:150] if p.content else 'بدون محتوى',
            'media_type': 'post' if p.media_type in ['post', 'منشور'] or p.parent_post is None else 'comment',
            'sentiment': sentiment.label if sentiment else 'غير محلل',
            'topic': tag.topic_label if tag else ('غير محدد' if p.media_type in ['post', 'منشور'] or p.parent_post is None else ''),
            'engine_used': sentiment.engine_used if sentiment else 'غير معروف',
            'confidence': sentiment.confidence_score if sentiment else 0.0,
            'posted_at': p.posted_at.strftime('%Y-%m-%d %H:%M') if p.posted_at else 'غير محدد'
        })
        
    return Response(log_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_batch_ai_topics(request):
    """
    يقوم بتشغيل ذكاء Gemini الاصطناعي المجمع لتصنيف مواضيع المنشورات الأصلية التي لم تُصنف بالذكاء الاصطناعي بعد.
    يضمن حظر إرسال أي منشور للـ AI مرتين بشكل قاطع.
    """
    from .sentiment_engine import batch_ai_topic_modeling
    import os
    
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        return Response(
            {
                'error': 'مفتاح Gemini غير موجود. أضف GEMINI_API_KEY (أو ai_key) في متغيرات البيئة على السيرفر.',
            },
            status=400,
        )
        
    # Exclude posts where sentiment engine_used contains 'Gemini' or 'Batch'
    posts = Post.objects.filter(
        profile__user=request.user,
        media_type='post'
    ).exclude(
        sentiments__engine_used__icontains='Gemini'
    ).exclude(
        sentiments__engine_used__icontains='Batch'
    )
    
    count = posts.count()
    if count == 0:
        return Response({
            'message': 'جميع المنشورات مصنفة بالذكاء الاصطناعي بالفعل ولا توجد بوستات جديدة بحاجة للإرسال.',
            'updated_count': 0
        })
        
    posts_data = [{"id": p.id, "content": p.content[:400]} for p in posts]
    
    try:
        batch_results = batch_ai_topic_modeling(posts_data, api_key)
        results_map = {}
        for item in batch_results:
            if "id" in item:
                try:
                    results_map[int(item["id"])] = item
                except (ValueError, TypeError):
                    results_map[item["id"]] = item
        
        updated_count = 0
        for post in posts:
            ai_res = results_map.get(post.id)
            if ai_res:
                ai_topic = ai_res.get("topic", "عام")
                sent_res = post.sentiments.first()
                if sent_res:
                    # Update engine_used to mark it as analyzed by Gemini Topic modeling, preventing any re-sending!
                    sent_res.engine_used = "Gemini 2.0 Flash (Batch Topic)"
                    sent_res.save()
                    
                    tag = sent_res.tags.first()
                    if tag:
                        tag.topic_label = ai_topic
                        tag.save()
                        updated_count += 1
                        
        return Response({
            'message': f'تم استخراج وتصنيف مواضيع {updated_count} منشوراً بنجاح عبر الذكاء الاصطناعي المجمع!',
            'updated_count': updated_count
        })
    except Exception as e:
        return Response({'error': f'فشل تصنيف المواضيع مجمعاً: {str(e)}'}, status=500)
