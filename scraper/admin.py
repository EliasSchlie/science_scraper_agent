from django.contrib import admin
from .models import Workspace, Interaction, ScraperJob


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'initial_variable', 'created_at', 'updated_at')
    search_fields = ('name', 'initial_variable')
    ordering = ('-created_at',)


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('workspace', 'independent_variable', 'dependent_variable', 'effect', 'reference', 'date_published', 'created_at')
    list_filter = ('effect', 'workspace', 'created_at')
    search_fields = ('independent_variable', 'dependent_variable', 'reference')
    ordering = ('-created_at',)


@admin.register(ScraperJob)
class ScraperJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'workspace', 'variable_of_interest', 'status', 'interactions_found', 'papers_checked', 'started_at', 'completed_at')
    list_filter = ('status', 'workspace', 'started_at')
    search_fields = ('variable_of_interest',)
    readonly_fields = ('started_at', 'completed_at')
    ordering = ('-started_at',)

