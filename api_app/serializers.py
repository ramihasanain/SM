from rest_framework import serializers
from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification
)

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'business_domain', 'plan_type', 'report_schedule', 'timezone']

class SocialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialProfile
        fields = '__all__'

class PaymentTxnSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTxn
        fields = '__all__'

class ScrapeJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScrapeJob
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'

class PlatformMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlatformMeta
        fields = '__all__'

class AnalysisBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisBatch
        fields = '__all__'

class AIModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIModel
        fields = '__all__'

class SentimentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentResult
        fields = '__all__'

class TopicTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicTag
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
