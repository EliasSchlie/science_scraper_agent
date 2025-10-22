"""
Management command to mark stuck running jobs as failed
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from scraper.models import ScraperJob


class Command(BaseCommand):
    help = 'Mark stuck running jobs as failed'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=2,
            help='Mark jobs as stuck if running for more than this many hours (default: 2)',
        )

    def handle(self, *args, **options):
        hours = options['hours']
        cutoff_time = timezone.now() - timezone.timedelta(hours=hours)
        
        stuck_jobs = ScraperJob.objects.filter(
            status='running',
            started_at__lt=cutoff_time
        )
        
        count = stuck_jobs.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No stuck jobs found.'))
            return
        
        for job in stuck_jobs:
            job.status = 'failed'
            job.error_message = f'Job was stuck in running state for more than {hours} hours'
            job.completed_at = timezone.now()
            job.add_log(f'Job marked as failed (stuck for {hours}+ hours)')
            job.save()
            self.stdout.write(
                self.style.WARNING(f'Marked job {job.id} ({job.variable_of_interest}) as failed')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully marked {count} stuck job(s) as failed.')
        )

