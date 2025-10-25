from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """User profile with credits for compute usage"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    credits = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)

    def __str__(self):
        return f"{self.user.username} - {self.credits} credits"

    def has_credits(self, amount):
        """Check if user has enough credits"""
        from decimal import Decimal
        amount = Decimal(str(amount))
        return self.credits >= amount

    def deduct_credits(self, amount):
        """Deduct credits from user account"""
        from decimal import Decimal
        amount = Decimal(str(amount))
        if self.has_credits(amount):
            self.credits -= amount
            self.save(update_fields=['credits'])
            return True
        return False

    def add_credits(self, amount):
        """Add credits to user account"""
        from decimal import Decimal
        amount = Decimal(str(amount))
        self.credits += amount
        self.save(update_fields=['credits'])


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Auto-create profile when user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Interaction(models.Model):
    """Stores extracted interactions from scientific papers"""
    workspace = models.CharField(max_length=100, default='default', db_index=True)
    job = models.ForeignKey('ScraperJob', on_delete=models.CASCADE, related_name='interactions', null=True, blank=True)
    independent_variable = models.CharField(max_length=500)
    dependent_variable = models.CharField(max_length=500)
    effect = models.CharField(max_length=10)  # '+' or '-'
    reference = models.CharField(max_length=500)  # DOI
    date_published = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['workspace', '-created_at']),
        ]
    
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

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scraper_jobs', null=True)
    workspace = models.CharField(max_length=100, default='default', db_index=True)
    variable_of_interest = models.CharField(max_length=500)
    credits_cost = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    min_interactions = models.IntegerField(default=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    interactions_found = models.IntegerField(default=0)
    papers_checked = models.IntegerField(default=0)
    current_step = models.TextField(blank=True)
    logs = models.TextField(blank=True, default='')  # NEW: Accumulate all logs
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    stop_requested = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['workspace', '-started_at']),
        ]
    
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

