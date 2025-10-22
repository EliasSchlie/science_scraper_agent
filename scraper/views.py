from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_GET, require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Interaction, ScraperJob
from .services import start_scraper_job_async
import json


def scraper_home(request):
    """Main scraper interface"""
    recent_jobs = ScraperJob.objects.all()[:10]
    total_interactions = Interaction.objects.count()
    
    context = {
        'recent_jobs': recent_jobs,
        'total_interactions': total_interactions,
    }
    return render(request, 'scraper/home.html', context)


@require_POST
@csrf_exempt
def start_job(request):
    """Start a new scraper job"""
    try:
        data = json.loads(request.body)
        variable_of_interest = data.get('variable_of_interest', '').strip()
        min_interactions = int(data.get('min_interactions', 5))
        
        if not variable_of_interest:
            return JsonResponse({'error': 'Variable of interest is required'}, status=400)
        
        # Create job
        job = ScraperJob.objects.create(
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
        'logs': job.logs,  # NEW: Send all accumulated logs
        'error_message': job.error_message,
        'started_at': job.started_at.isoformat(),
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
    })


@require_GET
def interactions_list(request):
    """Get list of all interactions"""
    interactions = Interaction.objects.all()[:100]  # Limit to 100 most recent
    
    data = [{
        'id': i.id,
        'independent_variable': i.independent_variable,
        'dependent_variable': i.dependent_variable,
        'effect': i.effect,
        'reference': i.reference,
        'date_published': i.date_published,
        'created_at': i.created_at.isoformat(),
    } for i in interactions]
    
    return JsonResponse({'interactions': data, 'total': Interaction.objects.count()})


@require_GET
def job_interactions(request, job_id):
    """Get interactions for a specific job (by time range)"""
    job = get_object_or_404(ScraperJob, id=job_id)
    
    # Get interactions created during this job's run
    if job.completed_at:
        interactions = Interaction.objects.filter(
            created_at__gte=job.started_at,
            created_at__lte=job.completed_at
        )
    else:
        interactions = Interaction.objects.filter(
            created_at__gte=job.started_at
        )
    
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
        from django.utils import timezone
        job.status = 'failed'
        job.error_message = 'Job stopped by user'
        job.completed_at = timezone.now()
        job.add_log('Job stopped by user')
        job.save()
        
        return JsonResponse({'message': 'Job stopped successfully', 'status': job.status})
    else:
        return JsonResponse({'error': 'Job is not running'}, status=400)

