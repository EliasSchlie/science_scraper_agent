from django.urls import path
from . import views

app_name = 'scraper'

urlpatterns = [
    # Main graph view
    path('', views.graph_view, name='graph_view'),
    
    # Workspace management
    path('api/workspace/create/', views.create_workspace, name='create_workspace'),
    path('api/workspace/<int:workspace_id>/', views.workspace_data, name='workspace_data'),
    path('api/workspace/<int:workspace_id>/expand/', views.expand_variable, name='expand_variable'),
    path('api/workspace/<int:workspace_id>/jobs/', views.workspace_jobs, name='workspace_jobs'),
    path('api/workspace/<int:workspace_id>/delete/', views.delete_workspace, name='delete_workspace'),
    
    # Job management
    path('api/job/<int:job_id>/status/', views.job_status, name='job_status'),
    path('api/job/<int:job_id>/status/stream/', views.job_status_stream, name='job_status_stream'),
    path('api/job/<int:job_id>/stop/', views.stop_job, name='stop_job'),
]
