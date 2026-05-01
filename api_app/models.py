from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Overriding standard user model to add ERD fields
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    business_domain = models.CharField(max_length=255, null=True, blank=True)
    plan_type = models.CharField(max_length=50, null=True, blank=True)
    report_schedule = models.CharField(max_length=50, null=True, blank=True)
    timezone = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.username} - {self.email}"


class SocialProfile(models.Model):
    PLATFORM_CHOICES = (
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='social_profiles')
    platform = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    url = models.URLField(max_length=500, null=True, blank=True)
    is_competitor = models.BooleanField(default=False)
    platform_account_id = models.CharField(max_length=255, null=True, blank=True)
    account_name = models.CharField(max_length=255, null=True, blank=True)
    profile_picture_url = models.URLField(max_length=1000, null=True, blank=True)
    followers_count = models.IntegerField(default=0)
    access_token = models.TextField(null=True, blank=True)
    refresh_token = models.TextField(null=True, blank=True)
    token_expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.platform} Profile for {self.user.username}"


class PaymentTxn(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    method = models.CharField(max_length=50, default='bank_transfer') 
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    plan_selected = models.CharField(max_length=100, null=True, blank=True)
    receipt_image = models.ImageField(upload_to='receipts/', null=True, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} - {self.status}"


class ScrapeJob(models.Model):
    JOB_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    profile = models.ForeignKey(SocialProfile, on_delete=models.CASCADE, related_name='scrape_jobs')
    airflow_dag_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=50, choices=JOB_STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(null=True, blank=True)
    records_fetched = models.IntegerField(default=0)


class Post(models.Model):
    # BIGINT based on schema for post_id
    id = models.BigAutoField(primary_key=True) 
    parent_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author_name = models.CharField(max_length=255, null=True, blank=True)
    profile = models.ForeignKey(SocialProfile, on_delete=models.CASCADE, related_name='posts')
    job = models.ForeignKey(ScrapeJob, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts')
    content = models.TextField()
    detected_lang = models.CharField(max_length=10, null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    media_type = models.CharField(max_length=50, null=True, blank=True)
    engagement_json = models.JSONField(null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)


class Reaction(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    author_name = models.CharField(max_length=255)
    reaction_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class PlatformMeta(models.Model):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='platform_meta')
    hashtags = models.JSONField(null=True, blank=True)
    tweet_type = models.CharField(max_length=50, null=True, blank=True)


class AnalysisBatch(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='analysis_batches')
    trigger_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    started_at = models.DateTimeField(auto_now_add=True)
    posts_analyzed = models.IntegerField(default=0)


class AIModel(models.Model):
    model_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    lang = models.CharField(max_length=50, null=True, blank=True)
    provider = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)


class SentimentResult(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='sentiments')
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name='sentiments')
    batch = models.ForeignKey(AnalysisBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='sentiments')
    label = models.CharField(max_length=50) # pos, neg, neu
    pos_score = models.FloatField(null=True, blank=True)
    neg_score = models.FloatField(null=True, blank=True)
    neu_score = models.FloatField(null=True, blank=True)
    lang_processed = models.CharField(max_length=10, null=True, blank=True)
    analyzed_at = models.DateTimeField(auto_now_add=True)


class TopicTag(models.Model):
    result = models.ForeignKey(SentimentResult, on_delete=models.CASCADE, related_name='tags')
    topic_label = models.CharField(max_length=255)
    confidence = models.FloatField(null=True, blank=True)


class Report(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reports')
    type = models.CharField(max_length=50)
    period_from = models.DateField(null=True, blank=True)
    period_to = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50)
    format = models.CharField(max_length=50)
    file_url = models.TextField(null=True, blank=True)


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=50)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
