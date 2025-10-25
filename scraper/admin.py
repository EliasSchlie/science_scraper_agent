from django.contrib import admin
from .models import Interaction, ScraperJob, UserProfile


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('independent_variable', 'dependent_variable', 'effect', 'reference', 'date_published', 'created_at')
    list_filter = ('effect', 'created_at')
    search_fields = ('independent_variable', 'dependent_variable', 'reference')
    ordering = ('-created_at',)


@admin.register(ScraperJob)
class ScraperJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'variable_of_interest', 'user', 'status', 'credits_cost', 'interactions_found', 'papers_checked', 'started_at', 'completed_at')
    list_filter = ('status', 'started_at')
    search_fields = ('variable_of_interest', 'user__username')
    readonly_fields = ('started_at', 'completed_at')
    ordering = ('-started_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits')
    search_fields = ('user__username', 'user__email')
    ordering = ('user__username',)

