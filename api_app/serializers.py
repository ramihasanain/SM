from rest_framework import serializers
from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification
)

class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'password', 'company_name', 'country', 'phone_number', 'business_domain', 'plan_type', 'report_schedule', 'timezone']

    def validate_password(self, value):
        if not value:
            return value
        
        import re
        
        # 1. Length check
        if len(value) < 8:
            raise serializers.ValidationError("يجب أن تكون كلمة المرور مكونة من 8 رموز على الأقل.")
            
        # 2. Lowercase letter
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("يجب أن تحتوي كلمة المرور على حرف صغير واحد على الأقل.")
            
        # 3. Uppercase letter
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("يجب أن تحتوي كلمة المرور على حرف كبير واحد على الأقل.")
            
        # 4. Digit
        if not re.search(r"\d", value):
            raise serializers.ValidationError("يجب أن تحتوي كلمة المرور على رقم واحد على الأقل.")
            
        # 5. Special character
        if not re.search(r"[@$!%*?&#^()_\-+={[\]}|:;\"'<>,./?`~]", value):
            raise serializers.ValidationError("يجب أن تحتوي كلمة المرور على رمز خاص واحد على الأقل (مثل @، $، !، %، *، ?، &).")
            
        # 6. Check for simple repetition or sequences
        if len(set(value)) <= 2:
            raise serializers.ValidationError("كلمة المرور بسيطة جداً وتتكون من أحرف متكررة.")
            
        # 7. Check for simple digit sequence, like '12345678', '87654321'
        digits = re.sub(r"\D", "", value)
        if digits:
            for i in range(len(digits) - 4):
                seq = digits[i:i+5]
                if seq in "01234567890" or seq in "98765432109":
                    raise serializers.ValidationError("لا يسمح بكلمات المرور التي تحتوي على أرقام متسلسلة عادية (مثل 12345).")
                    
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CustomUser(**validated_data)
        if password is not None:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password is not None and password != "":
            instance.set_password(password)
        instance.save()
        return instance

class SocialProfileSerializer(serializers.ModelSerializer):
    posts_count = serializers.SerializerMethodField()

    class Meta:
        model = SocialProfile
        fields = '__all__'

    def get_posts_count(self, obj):
        return obj.posts.filter(media_type='post').count()

class PaymentTxnSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTxn
        fields = '__all__'

class ScrapeJobSerializer(serializers.ModelSerializer):
    profile_name = serializers.CharField(source='profile.account_name', read_only=True)
    platform = serializers.CharField(source='profile.platform', read_only=True)

    class Meta:
        model = ScrapeJob
        fields = '__all__'

class PostSerializer(serializers.ModelSerializer):
    sentiment = serializers.SerializerMethodField()
    topic = serializers.SerializerMethodField()
    platform = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()
    
    # New Sarcasm and Hybrid Engine Serializer Fields
    is_sarcastic = serializers.SerializerMethodField()
    sarcasm_explanation = serializers.SerializerMethodField()
    engine_used = serializers.SerializerMethodField()
    is_analyzed = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = '__all__'

    def _get_first_sentiment(self, obj):
        if not hasattr(obj, '_first_sentiment_cached'):
            # Access prefetched queryset in memory
            sentiments = list(obj.sentiments.all())
            obj._first_sentiment_cached = sentiments[0] if sentiments else None
        return obj._first_sentiment_cached

    def get_is_analyzed(self, obj):
        sentiment = self._get_first_sentiment(obj)
        return sentiment is not None

    def get_sentiment(self, obj):
        sentiment = self._get_first_sentiment(obj)
        return sentiment.label if sentiment else "محايد"

    def get_score(self, obj):
        sentiment = self._get_first_sentiment(obj)
        if sentiment:
            if sentiment.label == 'إيجابي': return sentiment.pos_score
            if sentiment.label == 'سلبي': return sentiment.neg_score
            return sentiment.neu_score
        return 0.5

    def get_topic(self, obj):
        if obj.media_type == 'comment':
            return ""
        sentiment = self._get_first_sentiment(obj)
        if sentiment:
            tags = list(sentiment.tags.all())
            return tags[0].topic_label if tags else "غير محدد"
        return "غير محدد"

    def get_platform(self, obj):
        return obj.profile.platform if obj.profile else "facebook"
        
    def get_is_sarcastic(self, obj):
        sentiment = self._get_first_sentiment(obj)
        return sentiment.is_sarcastic if sentiment else False

    def get_sarcasm_explanation(self, obj):
        sentiment = self._get_first_sentiment(obj)
        return sentiment.sarcasm_explanation if sentiment else ""

    def get_engine_used(self, obj):
        sentiment = self._get_first_sentiment(obj)
        return sentiment.engine_used if sentiment else "Local Lexicon"

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
