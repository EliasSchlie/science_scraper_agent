from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction, ScraperJob, Workspace
from .services import start_scraper_job_async
import json
import time


def graph_view(request):
    """Main graph view - the only page"""
    workspaces = Workspace.objects.all()[:10]
    
    context = {
        'workspaces': workspaces,
    }
    return render(request, 'scraper/graph_view.html', context)


@require_POST
@csrf_exempt
def create_workspace(request):
    """Create a new workspace and start initial search"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        initial_variable = data.get('initial_variable', '').strip()
        min_interactions = int(data.get('min_interactions', 5))
        
        if not name or not initial_variable:
            return JsonResponse({'error': 'Name and initial variable are required'}, status=400)
        
        # Create workspace
        workspace = Workspace.objects.create(
            name=name,
            initial_variable=initial_variable
        )
        
        # Create job to search for initial variable
        job = ScraperJob.objects.create(
            workspace=workspace,
            variable_of_interest=initial_variable,
            min_interactions=min_interactions,
            status='pending'
        )
        
        # Start scraping in background
        start_scraper_job_async(job.id)
        
        return JsonResponse({
            'workspace_id': workspace.id,
            'job_id': job.id,
            'message': 'Workspace created and search started'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
@csrf_exempt
def expand_variable(request, workspace_id):
    """Expand a variable in the graph by searching for its interactions"""
    try:
        data = json.loads(request.body)
        variable = data.get('variable', '').strip()
        min_interactions = int(data.get('min_interactions', 5))
        
        if not variable:
            return JsonResponse({'error': 'Variable is required'}, status=400)
        
        workspace = get_object_or_404(Workspace, id=workspace_id)
        
        # Create job to search for this variable
        job = ScraperJob.objects.create(
            workspace=workspace,
            variable_of_interest=variable,
            min_interactions=min_interactions,
            status='pending'
        )
        
        # Start scraping in background
        start_scraper_job_async(job.id)
        
        return JsonResponse({
            'job_id': job.id,
            'message': f'Started searching for interactions with {variable}'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def workspace_data(request, workspace_id):
    """Get all interactions for a workspace (for graph visualization)"""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    interactions = workspace.interactions.filter(effect__in=['+', '-'])
    
    data = [{
        'id': i.id,
        'independent_variable': i.independent_variable,
        'dependent_variable': i.dependent_variable,
        'effect': i.effect,
        'reference': i.reference,
        'date_published': i.date_published,
    } for i in interactions]
    
    return JsonResponse({
        'workspace': {
            'id': workspace.id,
            'name': workspace.name,
            'initial_variable': workspace.initial_variable,
        },
        'interactions': data,
        'count': len(data)
    })


@require_GET
def job_status(request, job_id):
    """Get job status and progress"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    return JsonResponse({
        'id': job.id,
        'workspace_id': job.workspace.id if job.workspace else None,
        'variable_of_interest': job.variable_of_interest,
        'status': job.status,
        'interactions_found': job.interactions_found,
        'papers_checked': job.papers_checked,
        'current_step': job.current_step,
        'logs': job.logs,
        'error_message': job.error_message,
        'started_at': job.started_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'stop_requested': job.stop_requested,
    })


@require_POST
@csrf_exempt
def stop_job(request, job_id):
    """Stop a running job"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    if job.status == 'running':
        job.stop_requested = True
        job.add_log('Stop requested by user')
        job.save(update_fields=['stop_requested', 'logs', 'current_step'])
        return JsonResponse({'message': 'Stop requested. Job will halt shortly.', 'status': job.status})
    else:
        return JsonResponse({'error': 'Job is not running'}, status=400)


@require_GET
def workspace_jobs(request, workspace_id):
    """Get all jobs for a workspace"""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    jobs = workspace.jobs.all()[:20]
    
    data = [{
        'id': job.id,
        'variable_of_interest': job.variable_of_interest,
        'status': job.status,
        'interactions_found': job.interactions_found,
        'papers_checked': job.papers_checked,
        'started_at': job.started_at.isoformat(),
    } for job in jobs]
    
    return JsonResponse({'jobs': data})


@require_POST
@csrf_exempt
def delete_workspace(request, workspace_id):
    """Delete a workspace and all its data"""
    workspace = get_object_or_404(Workspace, id=workspace_id)
    name = workspace.name
    workspace.delete()
    return JsonResponse({'message': f'Workspace "{name}" deleted successfully'})


@require_GET
def job_status_stream(request, job_id):
    """Stream job status updates via Server-Sent Events"""
    def event_stream():
        job = get_object_or_404(ScraperJob, id=job_id)
        last_log_length = 0

        while True:
            # Refresh job from database
            job.refresh_from_db()

            # Send status update
            data = {
                'status': job.status,
                'interactions_found': job.interactions_found,
                'papers_checked': job.papers_checked,
                'current_step': job.current_step,
                'logs': job.logs[last_log_length:],  # Only new logs
                'error_message': job.error_message,
                'stop_requested': job.stop_requested,
            }

            last_log_length = len(job.logs)

            yield f"data: {json.dumps(data)}\n\n"

            # Stop streaming if job is finished
            if job.status in ['completed', 'failed']:
                break

            # Wait before next update
            time.sleep(0.5)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
