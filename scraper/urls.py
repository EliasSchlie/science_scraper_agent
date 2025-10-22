from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    path('', views.scraper_home, name='home'),
    path('api/start/', views.start_job, name='start_job'),
    path('api/job/<int:job_id>/status/', views.job_status, name='job_status'),
    path('api/job/<int:job_id>/interactions/', views.job_interactions, name='job_interactions'),
    path('api/interactions/', views.interactions_list, name='interactions_list'),
]

