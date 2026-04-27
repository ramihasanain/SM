from rest_framework import serializers
from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification
)

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'business_domain', 'plan_type', 'report_schedule', 'timezone']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user

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
    sentiment = serializers.SerializerMethodField()
    topic = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'

    def get_sentiment(self, obj):
        sentiment = obj.sentiments.first()
        return sentiment.label if sentiment else "محايد"

    def get_score(self, obj):
        sentiment = obj.sentiments.first()
        if sentiment:
            if sentiment.label == 'إيجابي': return sentiment.pos_score
            if sentiment.label == 'سلبي': return sentiment.neg_score
            return sentiment.neu_score
        return 0.5

    def get_topic(self, obj):
        sentiment = obj.sentiments.first()
        if sentiment:
            tag = sentiment.tags.first()
            return tag.topic_label if tag else "غير محدد"
        return "غير محدد"

    def get_platform(self, obj):
        return obj.profile.platform if obj.profile else "facebook"

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
