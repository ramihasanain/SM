from django.urls import path
from . import views

urlpatterns = [
    # 1. User
    path('users/', views.user_list_create, name='user-list'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),
    
    # 2. Social Profile
    path('profiles/', views.profile_list_create, name='profile-list'),
    path('profiles/<int:pk>/', views.profile_detail, name='profile-detail'),

    # 3. Payment Txn
    path('payments/', views.payment_txn_list_create, name='payment-list'),
    path('payments/<int:pk>/', views.payment_txn_detail, name='payment-detail'),

    # 4. Scrape Job
    path('scrape-jobs/', views.scrape_job_list_create, name='scrape-job-list'),
    path('scrape-jobs/<int:pk>/', views.scrape_job_detail, name='scrape-job-detail'),

    # 5. Post
    path('posts/', views.post_list_create, name='post-list'),
    path('posts/<int:pk>/', views.post_detail, name='post-detail'),

    # 6. Platform Meta
    path('platform-metas/', views.platform_meta_list_create, name='platform-meta-list'),
    path('platform-metas/<int:pk>/', views.platform_meta_detail, name='platform-meta-detail'),

    # 7. Analysis Batch
    path('analysis-batches/', views.analysis_batch_list_create, name='analysis-batch-list'),
    path('analysis-batches/<int:pk>/', views.analysis_batch_detail, name='analysis-batch-detail'),

    # 8. AI Model
    path('ai-models/', views.ai_model_list_create, name='ai-model-list'),
    path('ai-models/<int:pk>/', views.ai_model_detail, name='ai-model-detail'),

    # 9. Sentiment Result
    path('sentiment-results/', views.sentiment_result_list_create, name='sentiment-result-list'),
    path('sentiment-results/<int:pk>/', views.sentiment_result_detail, name='sentiment-result-detail'),

    # 10. Topic Tag
    path('topic-tags/', views.topic_tag_list_create, name='topic-tag-list'),
    path('topic-tags/<int:pk>/', views.topic_tag_detail, name='topic-tag-detail'),

    # 11. Report
    path('reports/', views.report_list_create, name='report-list'),
    path('reports/<int:pk>/', views.report_detail, name='report-detail'),

    # 12. Notification
    path('notifications/', views.notification_list_create, name='notification-list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification-detail'),
]
