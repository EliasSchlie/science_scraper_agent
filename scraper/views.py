from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction, ScraperJob
from .services import start_scraper_job_async
import json


def get_current_workspace(request):
    """Get current workspace from session, defaulting to 'default'"""
    return request.session.get('workspace', 'default')


def scraper_home(request):
    """Main scraper interface"""
    workspace = get_current_workspace(request)
    recent_jobs = ScraperJob.objects.filter(workspace=workspace)[:10]
    total_interactions = Interaction.objects.filter(workspace=workspace).count()
    
    # Get list of all workspaces
    all_workspaces = list(ScraperJob.objects.values_list('workspace', flat=True).distinct())
    if 'default' not in all_workspaces:
        all_workspaces.insert(0, 'default')
    
    context = {
        'recent_jobs': recent_jobs,
        'total_interactions': total_interactions,
        'current_workspace': workspace,
        'all_workspaces': all_workspaces,
    }
    return render(request, 'scraper/home.html', context)


def graph_view(request):
    """Network graph visualization"""
    workspace = get_current_workspace(request)
    
    # Get list of all workspaces
    all_workspaces = list(ScraperJob.objects.values_list('workspace', flat=True).distinct())
    if 'default' not in all_workspaces:
        all_workspaces.insert(0, 'default')
    
    # Check if workspace has interactions
    has_interactions = Interaction.objects.filter(workspace=workspace).exists()
    
    context = {
        'current_workspace': workspace,
        'all_workspaces': all_workspaces,
        'has_interactions': has_interactions,
    }
    return render(request, 'scraper/graph_view.html', context)


@require_POST
@csrf_exempt
def start_job(request):
    """Start a new scraper job"""
    try:
        data = json.loads(request.body)
        variable_of_interest = data.get('variable_of_interest', '').strip()
        min_interactions = int(data.get('min_interactions', 5))
        workspace = get_current_workspace(request)
        
        if not variable_of_interest:
            return JsonResponse({'error': 'Variable of interest is required'}, status=400)
        
        # Create job
        job = ScraperJob.objects.create(
            workspace=workspace,
            variable_of_interest=variable_of_interest,
            min_interactions=min_interactions,
            status='pending'
        )
        
        # Start in background
        start_scraper_job_async(job.id)
        
        return JsonResponse({
            'job_id': job.id,
            'status': job.status,
            'message': 'Job started successfully'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def job_status(request, job_id):
    """Get job status and progress"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    return JsonResponse({
        'id': job.id,
        'variable_of_interest': job.variable_of_interest,
        'status': job.status,
        'interactions_found': job.interactions_found,
        'papers_checked': job.papers_checked,
        'current_step': job.current_step,
        'logs': job.logs,  # accumulated logs
        'error_message': job.error_message,
        'started_at': job.started_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'stop_requested': job.stop_requested,
    })


@require_GET
def interactions_list(request):
    """Get list of all interactions for current workspace"""
    workspace = get_current_workspace(request)
    interactions = Interaction.objects.filter(workspace=workspace, effect__in=['+', '-'])[:100]  # Only valid effects
    
    data = [{
        'id': i.id,
        'independent_variable': i.independent_variable,
        'dependent_variable': i.dependent_variable,
        'effect': i.effect,
        'reference': i.reference,
        'date_published': i.date_published,
        'created_at': i.created_at.isoformat(),
    } for i in interactions]
    
    return JsonResponse({
        'interactions': data, 
        'total': Interaction.objects.filter(workspace=workspace, effect__in=['+', '-']).count()
    })


@require_GET
def job_interactions(request, job_id):
    """Get interactions for a specific job"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    # Get interactions linked to this job
    interactions = Interaction.objects.filter(job=job, effect__in=['+', '-'])
    
    data = [{
        'id': i.id,
        'independent_variable': i.independent_variable,
        'dependent_variable': i.dependent_variable,
        'effect': i.effect,
        'reference': i.reference,
        'date_published': i.date_published,
    } for i in interactions]
    
    return JsonResponse({'interactions': data, 'count': len(data)})


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


@require_POST
@csrf_exempt
def delete_job(request, job_id):
    """Delete a job and its associated data"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    # Check if force delete is requested
    force = request.POST.get('force') == 'true' or json.loads(request.body or '{}').get('force') == True
    
    # Only allow deleting non-running jobs unless force is true
    if job.status == 'running' and not force:
        return JsonResponse({
            'error': 'Job appears to be running. If the job is stuck, you can force delete it.',
            'can_force': True
        }, status=400)
    
    job.delete()
    return JsonResponse({'message': 'Job deleted successfully'})


@require_POST
@csrf_exempt
def switch_workspace(request):
    """Switch to a different workspace"""
    try:
        data = json.loads(request.body)
        workspace = data.get('workspace', 'default').strip()
        
        if not workspace:
            return JsonResponse({'error': 'Workspace name is required'}, status=400)
        
        # Store in session
        request.session['workspace'] = workspace
        
        return JsonResponse({
            'workspace': workspace,
            'message': f'Switched to workspace: {workspace}'
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def list_workspaces(request):
    """Get list of all workspaces"""
    workspaces = list(ScraperJob.objects.values_list('workspace', flat=True).distinct())
    if 'default' not in workspaces:
        workspaces.insert(0, 'default')
    
    current_workspace = get_current_workspace(request)
    
    return JsonResponse({
        'workspaces': workspaces,
        'current': current_workspace
    })

