from django.db import models
from django.utils import timezone


class Interaction(models.Model):
    """Stores extracted interactions from scientific papers"""
    independent_variable = models.CharField(max_length=500)
    dependent_variable = models.CharField(max_length=500)
    effect = models.CharField(max_length=10)  # '+' or '-'
    reference = models.CharField(max_length=500)  # DOI
    date_published = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.independent_variable} -> {self.dependent_variable} ({self.effect})"


class ScraperJob(models.Model):
    """Tracks scraper job execution and progress"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    variable_of_interest = models.CharField(max_length=500)
    min_interactions = models.IntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    interactions_found = models.IntegerField(default=0)
    papers_checked = models.IntegerField(default=0)
    current_step = models.TextField(blank=True)
    logs = models.TextField(blank=True, default='')  # NEW: Accumulate all logs
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Job {self.id}: {self.variable_of_interest} ({self.status})"
    
    def add_log(self, message):
        """Add a log entry with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.logs += log_entry
        self.current_step = message
        self.save(update_fields=['logs', 'current_step'])

