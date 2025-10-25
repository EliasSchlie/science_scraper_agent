from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    path('', views.scraper_home, name='home'),
    path('graph/', views.graph_view, name='graph_view'),
    path('api/start/', views.start_job, name='start_job'),
    path('api/job/<int:job_id>/status/', views.job_status, name='job_status'),
    path('api/job/<int:job_id>/interactions/', views.job_interactions, name='job_interactions'),
    path('api/job/<int:job_id>/stop/', views.stop_job, name='stop_job'),
    path('api/job/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('api/interactions/', views.interactions_list, name='interactions_list'),
    path('api/workspaces/', views.list_workspaces, name='list_workspaces'),
    path('api/workspace/switch/', views.switch_workspace, name='switch_workspace'),
    path('api/workspace/delete/', views.delete_workspace, name='delete_workspace'),
]

