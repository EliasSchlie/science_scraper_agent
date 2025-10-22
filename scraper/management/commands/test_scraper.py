"""
Django management command to test the scraper setup
Usage: python manage.py test_scraper
"""
from django.core.management.base import BaseCommand
from scraper.models import ScraperJob
from scraper.services import start_scraper_job_async
import time


class Command(BaseCommand):
    help = 'Test the scraper setup by running a small test job'

    def add_arguments(self, parser):
        parser.add_argument(
            '--variable',
            type=str,
            default='creatine',
            help='Variable of interest to search for (default: creatine)'
        )
        parser.add_argument(
            '--min-interactions',
            type=int,
            default=3,
            help='Minimum interactions to find (default: 3)'
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for job to complete and show results'
        )

    def handle(self, *args, **options):
        variable = options['variable']
        min_interactions = options['min_interactions']
        wait = options['wait']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Scientific Paper Scraper - Test Command'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        # Test 1: Check imports
        self.stdout.write('Test 1: Checking dependencies...')
        try:
            from langchain_nebius import ChatNebius
            from langgraph.graph import StateGraph
            import pymupdf4llm
            self.stdout.write(self.style.SUCCESS('✓ All dependencies installed'))
        except ImportError as e:
            self.stdout.write(self.style.ERROR(f'✗ Missing dependency: {e}'))
            return

        # Test 2: Check environment variables
        self.stdout.write('\nTest 2: Checking environment variables...')
        import os
        if os.environ.get('NEBIUS_API_KEY'):
            self.stdout.write(self.style.SUCCESS('✓ NEBIUS_API_KEY is set'))
        else:
            self.stdout.write(self.style.ERROR('✗ NEBIUS_API_KEY is not set'))
            self.stdout.write(self.style.WARNING('  Please set NEBIUS_API_KEY in your .env file'))
            return

        # Test 3: Check database
        self.stdout.write('\nTest 3: Checking database...')
        try:
            count = ScraperJob.objects.count()
            self.stdout.write(self.style.SUCCESS(f'✓ Database connected ({count} existing jobs)'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database error: {e}'))
            return

        # Test 4: Create test job
        self.stdout.write('\nTest 4: Creating test scraper job...')
        try:
            job = ScraperJob.objects.create(
                variable_of_interest=variable,
                min_interactions=min_interactions,
                status='pending'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Job created (ID: {job.id})'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to create job: {e}'))
            return

        # Test 5: Start job
        self.stdout.write('\nTest 5: Starting scraper job...')
        try:
            start_scraper_job_async(job.id)
            self.stdout.write(self.style.SUCCESS('✓ Job started in background'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed to start job: {e}'))
            return

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'Test job started successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(f'Job ID: {job.id}')
        self.stdout.write(f'Variable: {variable}')
        self.stdout.write(f'Target: {min_interactions} interactions')
        self.stdout.write('')
        self.stdout.write('You can monitor the job at:')
        self.stdout.write(f'  Web: http://localhost:8000/scraper/')
        self.stdout.write(f'  Admin: http://localhost:8000/admin/scraper/scraperjob/{job.id}/change/')
        self.stdout.write('')

        if wait:
            self.stdout.write('Waiting for job to complete...')
            self.stdout.write('(Press Ctrl+C to stop waiting)\n')
            
            try:
                while True:
                    time.sleep(5)
                    job.refresh_from_db()
                    
                    if job.current_step:
                        self.stdout.write(f'  {job.current_step}')
                    
                    if job.status in ['completed', 'failed']:
                        break
                
                self.stdout.write('')
                if job.status == 'completed':
                    self.stdout.write(self.style.SUCCESS('✓ Job completed successfully!'))
                    self.stdout.write(f'  Interactions found: {job.interactions_found}')
                    self.stdout.write(f'  Papers checked: {job.papers_checked}')
                else:
                    self.stdout.write(self.style.ERROR('✗ Job failed'))
                    self.stdout.write(f'  Error: {job.error_message}')
                    
            except KeyboardInterrupt:
                self.stdout.write('\n\nMonitoring stopped. Job continues in background.')
        else:
            self.stdout.write('Job is running in background.')
            self.stdout.write('Use --wait flag to monitor progress.')

