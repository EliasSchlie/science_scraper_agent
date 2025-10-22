from django.db import models
from django.utils import timezone


class Workspace(models.Model):
    """A workspace containing a graph of interactions"""
    name = models.CharField(max_length=200)
    initial_variable = models.CharField(max_length=500)  # The starting node
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Interaction(models.Model):
    """Stores extracted interactions from scientific papers"""
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
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
    
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='jobs', null=True, blank=True)
    variable_of_interest = models.CharField(max_length=500)  # The variable we're searching for
    min_interactions = models.IntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    interactions_found = models.IntegerField(default=0)
    papers_checked = models.IntegerField(default=0)
    current_step = models.TextField(blank=True)
    logs = models.TextField(blank=True, default='')
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    stop_requested = models.BooleanField(default=False)
    
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

