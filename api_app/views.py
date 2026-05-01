from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification
)
from .serializers import (
    CustomUserSerializer, SocialProfileSerializer, PaymentTxnSerializer, ScrapeJobSerializer, PostSerializer,
    PlatformMetaSerializer, AnalysisBatchSerializer, AIModelSerializer, SentimentResultSerializer, TopicTagSerializer, ReportSerializer, NotificationSerializer
)

# ==========================================================
# 1. USER VIEWS
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_me(request):
    serializer = CustomUserSerializer(request.user)
    return Response(serializer.data)

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
        items = SocialProfile.objects.filter(user=request.user)
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
def scrape_job_list_create(request):
    if request.method == 'GET':
        items = ScrapeJob.objects.all()
        serializer = ScrapeJobSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ScrapeJobSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def scrape_job_detail(request, pk):
    try:
        item = ScrapeJob.objects.get(pk=pk)
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
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def post_list_create(request):
    if request.method == 'GET':
        items = Post.objects.filter(profile__user=request.user)
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
def post_detail(request, pk):
    try:
        item = Post.objects.get(pk=pk)
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
def platform_meta_list_create(request):
    if request.method == 'GET':
        items = PlatformMeta.objects.all()
        serializer = PlatformMetaSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PlatformMetaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def platform_meta_detail(request, pk):
    try:
        item = PlatformMeta.objects.get(pk=pk)
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
def analysis_batch_list_create(request):
    if request.method == 'GET':
        items = AnalysisBatch.objects.all()
        serializer = AnalysisBatchSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = AnalysisBatchSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def analysis_batch_detail(request, pk):
    try:
        item = AnalysisBatch.objects.get(pk=pk)
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
def sentiment_result_list_create(request):
    if request.method == 'GET':
        items = SentimentResult.objects.all()
        serializer = SentimentResultSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = SentimentResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def sentiment_result_detail(request, pk):
    try:
        item = SentimentResult.objects.get(pk=pk)
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
def topic_tag_list_create(request):
    if request.method == 'GET':
        items = TopicTag.objects.all()
        serializer = TopicTagSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = TopicTagSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def topic_tag_detail(request, pk):
    try:
        item = TopicTag.objects.get(pk=pk)
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
def report_list_create(request):
    if request.method == 'GET':
        items = Report.objects.all()
        serializer = ReportSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = ReportSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def report_detail(request, pk):
    try:
        item = Report.objects.get(pk=pk)
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


# ==========================================================
# 12. NOTIFICATION VIEWS
# ==========================================================
@api_view(['GET', 'POST'])
def notification_list_create(request):
    if request.method == 'GET':
        items = Notification.objects.all()
        serializer = NotificationSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = NotificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def notification_detail(request, pk):
    try:
        item = Notification.objects.get(pk=pk)
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
    
    sentiments = SentimentResult.objects.filter(post__profile__user=request.user)
    total_sentiments = sentiments.count() or 1
    pos_count = sentiments.filter(label='إيجابي').count()
    neg_count = sentiments.filter(label='سلبي').count()
    neu_count = sentiments.filter(label='محايد').count()
    
    topics = TopicTag.objects.filter(result__post__profile__user=request.user).values('topic_label').annotate(count=Count('id')).order_by('-count')[:5]
    top_topics = []
    for t in topics:
        res = SentimentResult.objects.filter(tags__topic_label=t['topic_label'], post__profile__user=request.user).first()
        label = res.label if res else 'محايد'
        top_topics.append({
            'topic': t['topic_label'],
            'count': t['count'],
            'sentiment': label,
            'badge': 'badge-green' if label == 'إيجابي' else 'badge-red' if label == 'سلبي' else 'badge-amber'
        })
        
    fb_posts = total_posts_qs.filter(profile__platform='facebook').count()
    x_posts = total_posts_qs.filter(profile__platform='twitter').count()
    
    # Dynamic Timeline based on actual data dates (Last 30 days of available data)
    from django.db.models.functions import TruncDate
    
    daily_posts = total_posts_qs.annotate(date=TruncDate('posted_at')).values('date').annotate(count=Count('id')).order_by('-date')[:30]
    daily_comments = total_comments_qs.annotate(date=TruncDate('posted_at')).values('date').annotate(count=Count('id'))
    
    comments_dict = {str(item['date']): item['count'] for item in daily_comments if item['date']}
    
    timeline = []
    # Reverse to show chronological order (oldest to newest among the last 30 active days)
    for idx, item in enumerate(reversed(daily_posts)):
        if not item['date']: continue
        date_str = str(item['date'])
        timeline.append({
            'day': idx + 1,
            'date': date_str,
            'posts': item['count'],
            'comments': comments_dict.get(date_str, 0),
        })
        
    if not timeline:
        # Fallback to empty 30 days if no data
        now = timezone.now()
        for i in range(30):
            day = now - timedelta(days=29-i)
            timeline.append({
                'day': i + 1,
                'date': day.strftime('%Y-%m-%d'),
                'posts': 0,
                'comments': 0,
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
            'twitter': x_posts
        },
        'top_topics': top_topics,
        'timeline': timeline
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
            from .serializers import SocialProfileSerializer
            return Response({'message': 'Synced successfully', 'profile': SocialProfileSerializer(profile).data})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'error': 'Sync not implemented for this platform'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def post_details(request, pk):
    try:
        post = Post.objects.get(pk=pk)
    except Post.DoesNotExist:
        return Response({'error': 'Post not found'}, status=status.HTTP_404_NOT_FOUND)
        
    from .serializers import PostSerializer
    post_data = PostSerializer(post).data
    
    from .models import Reaction
    reactions = Reaction.objects.filter(post=post)
    reactions_list = [{'id': r.id, 'author_name': r.author_name, 'reaction_type': r.reaction_type} for r in reactions]
    
    comments = Post.objects.filter(parent_post=post, media_type='comment')
    comments_list = []
    for c in comments:
        c_data = PostSerializer(c).data
        comments_list.append({
            'id': c.id,
            'content': c.content,
            'author_name': c.author_name,
            'sentiment': c_data.get('sentiment', 'محايد'),
            'score': c_data.get('score', 0.5),
            'topic': c_data.get('topic', 'غير محدد')
        })
        
    return Response({
        'post': post_data,
        'reactions': reactions_list,
        'comments': comments_list
    })
