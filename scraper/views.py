from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Interaction, ScraperJob
from .services import start_scraper_job_async
import json


def get_current_workspace(request):
    """Get current workspace from session, defaulting to 'default'"""
    return request.session.get('workspace', 'default')


@login_required
def scraper_home(request):
    """Main scraper interface"""
    workspace = get_current_workspace(request)
    recent_jobs = ScraperJob.objects.filter(workspace=workspace, user=request.user)[:10]

    # Only count interactions from user's own jobs
    user_job_ids = ScraperJob.objects.filter(user=request.user, workspace=workspace).values_list('id', flat=True)
    total_interactions = Interaction.objects.filter(job_id__in=user_job_ids).count()

    # Get list of all workspaces for current user
    all_workspaces = list(ScraperJob.objects.filter(user=request.user).values_list('workspace', flat=True).distinct())
    if 'default' not in all_workspaces:
        all_workspaces.insert(0, 'default')

    context = {
        'recent_jobs': recent_jobs,
        'total_interactions': total_interactions,
        'current_workspace': workspace,
        'all_workspaces': all_workspaces,
    }
    return render(request, 'scraper/home.html', context)


@login_required
def graph_view(request):
    """Network graph visualization"""
    from django.contrib.auth.models import User

    workspace = get_current_workspace(request)

    # Get list of all workspaces for current user
    all_workspaces = list(ScraperJob.objects.filter(user=request.user).values_list('workspace', flat=True).distinct())
    if 'default' not in all_workspaces:
        all_workspaces.insert(0, 'default')

    # Check if workspace has interactions from user's jobs OR demo user's jobs
    user_job_ids = ScraperJob.objects.filter(user=request.user, workspace=workspace).values_list('id', flat=True)
    has_interactions = Interaction.objects.filter(job_id__in=user_job_ids).exists()

    # Also check if demo data exists (so button shows even if user has no data)
    if not has_interactions:
        demo_user = User.objects.filter(username='demo').first()
        if demo_user:
            demo_job_ids = ScraperJob.objects.filter(user=demo_user, workspace=workspace).values_list('id', flat=True)
            has_interactions = Interaction.objects.filter(job_id__in=demo_job_ids).exists()

    context = {
        'current_workspace': workspace,
        'all_workspaces': all_workspaces,
        'has_interactions': has_interactions,
    }
    return render(request, 'scraper/graph_view.html', context)


@require_POST
@csrf_exempt
@login_required
def start_job(request):
    """Start a new scraper job"""
    try:
        data = json.loads(request.body)
        variable_of_interest = data.get('variable_of_interest', '').strip()
        min_interactions = int(data.get('min_interactions', 5))
        workspace = get_current_workspace(request)
        credits_cost = float(min_interactions)  # 1 credit per interaction requested

        if not variable_of_interest:
            return JsonResponse({'error': 'Variable of interest is required'}, status=400)

        # Check if user has enough credits (but don't deduct yet)
        if not request.user.profile.has_credits(credits_cost):
            return JsonResponse({
                'error': f'Insufficient credits. You need {credits_cost} credits but have {request.user.profile.credits}.',
                'insufficient_credits': True
            }, status=400)

        # Create job (credits will be deducted on successful completion)
        job = ScraperJob.objects.create(
            user=request.user,
            workspace=workspace,
            variable_of_interest=variable_of_interest,
            min_interactions=min_interactions,
            credits_cost=credits_cost,
            status='pending'
        )

        # Start in background
        start_scraper_job_async(job.id)

        return JsonResponse({
            'job_id': job.id,
            'status': job.status,
            'message': f'Job started successfully. Will cost {credits_cost} credits if successful.',
            'credits_remaining': float(request.user.profile.credits)
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
@login_required
def job_status(request, job_id):
    """Get job status and progress"""
    workspace = get_current_workspace(request)
    job = get_object_or_404(ScraperJob, id=job_id, workspace=workspace, user=request.user)

    return JsonResponse({
        'id': job.id,
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


@require_GET
@login_required
def interactions_list(request):
    """Get list of all interactions for current workspace"""
    workspace = get_current_workspace(request)

    # Check if viewing demo/testing data
    view_demo = request.GET.get('demo') == 'true'

    if view_demo:
        # Show demo user's interactions (username: 'demo')
        from django.contrib.auth.models import User
        demo_user = User.objects.filter(username='demo').first()
        if demo_user:
            user_job_ids = ScraperJob.objects.filter(user=demo_user, workspace=workspace).values_list('id', flat=True)
        else:
            user_job_ids = []
    else:
        # Only show interactions from user's own jobs
        user_job_ids = ScraperJob.objects.filter(user=request.user, workspace=workspace).values_list('id', flat=True)

    interactions = Interaction.objects.filter(job_id__in=user_job_ids, effect__in=['+', '-'])[:100]

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
        'total': Interaction.objects.filter(job_id__in=user_job_ids, effect__in=['+', '-']).count()
    })


@require_GET
@login_required
def job_interactions(request, job_id):
    """Get interactions for a specific job"""
    workspace = get_current_workspace(request)
    job = get_object_or_404(ScraperJob, id=job_id, workspace=workspace, user=request.user)

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
@login_required
def stop_job(request, job_id):
    """Stop a running job"""
    workspace = get_current_workspace(request)
    job = get_object_or_404(ScraperJob, id=job_id, workspace=workspace, user=request.user)

    if job.status == 'running':
        job.stop_requested = True
        job.add_log('Stop requested by user')
        job.save(update_fields=['stop_requested', 'logs', 'current_step'])
        return JsonResponse({'message': 'Stop requested. Job will halt shortly.', 'status': job.status})
    else:
        return JsonResponse({'error': 'Job is not running'}, status=400)


@require_POST
@csrf_exempt
@login_required
def delete_job(request, job_id):
    """Delete a job and its associated data"""
    workspace = get_current_workspace(request)
    job = get_object_or_404(ScraperJob, id=job_id, workspace=workspace, user=request.user)

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
@login_required
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
@login_required
def list_workspaces(request):
    """Get list of all workspaces for current user"""
    workspaces = list(ScraperJob.objects.filter(user=request.user).values_list('workspace', flat=True).distinct())
    if 'default' not in workspaces:
        workspaces.insert(0, 'default')

    current_workspace = get_current_workspace(request)

    return JsonResponse({
        'workspaces': workspaces,
        'current': current_workspace
    })

