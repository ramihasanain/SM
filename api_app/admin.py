from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification
)

admin.site.register(CustomUser, UserAdmin)
admin.site.register(SocialProfile)
admin.site.register(PaymentTxn)
admin.site.register(ScrapeJob)
admin.site.register(Post)
admin.site.register(PlatformMeta)
admin.site.register(AnalysisBatch)
admin.site.register(AIModel)
admin.site.register(SentimentResult)
admin.site.register(TopicTag)
admin.site.register(Report)
admin.site.register(Notification)
