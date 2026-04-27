from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
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
# ==========================================================
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
def profile_list_create(request):
    if request.method == 'GET':
        items = SocialProfile.objects.all()
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
def payment_txn_list_create(request):
    if request.method == 'GET':
        items = PaymentTxn.objects.all()
        serializer = PaymentTxnSerializer(items, many=True)
        return Response(serializer.data)
    elif request.method == 'POST':
        serializer = PaymentTxnSerializer(data=request.data)
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
def post_list_create(request):
    if request.method == 'GET':
        items = Post.objects.all()
        serializer = PostSerializer(items, many=True)
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
