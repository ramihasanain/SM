from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, SocialProfile, PaymentTxn, ScrapeJob, Post, Reaction,
    PlatformMeta, AnalysisBatch, AIModel, SentimentResult, TopicTag, Report, Notification
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')

admin.site.register(CustomUser, CustomUserAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'content_snippet', 'media_type', 'author_name', 'posted_at')
    list_filter = ('media_type',)
    search_fields = ('content', 'author_name')
    
    def content_snippet(self, obj):
        return obj.content[:50] + '...' if obj.content else ''
    content_snippet.short_description = 'Content'

admin.site.register(Post, PostAdmin)

class Comment(Post):
    class Meta:
        proxy = True
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author_name', 'content_snippet', 'parent_post')
    search_fields = ('content', 'author_name')
    list_filter = ('author_name',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(media_type='comment')
        
    def content_snippet(self, obj):
        return obj.content[:50] + '...' if obj.content else ''
    content_snippet.short_description = 'Content'

admin.site.register(Comment, CommentAdmin)

class ReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'author_name', 'reaction_type', 'post')
    list_filter = ('reaction_type',)
    search_fields = ('author_name',)

admin.site.register(Reaction, ReactionAdmin)

admin.site.register(SocialProfile)
class PaymentTxnAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'method', 'status', 'plan_selected', 'paid_at')
    list_filter = ('status', 'method')
    search_fields = ('user__username', 'user__email')

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = PaymentTxn.objects.get(pk=obj.pk)
            if old_obj.status != 'approved' and obj.status == 'approved':
                # Approval triggered: Upgrade User Plan
                user = obj.user
                if obj.plan_selected:
                    user.plan_type = obj.plan_selected
                    user.save()
        super().save_model(request, obj, form, change)

admin.site.register(PaymentTxn, PaymentTxnAdmin)
admin.site.register(ScrapeJob)
admin.site.register(PlatformMeta)
admin.site.register(AnalysisBatch)
admin.site.register(AIModel)
admin.site.register(SentimentResult)
admin.site.register(TopicTag)
admin.site.register(Report)
admin.site.register(Notification)
