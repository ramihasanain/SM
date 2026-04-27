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
