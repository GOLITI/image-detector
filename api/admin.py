"""
Configuration de l'admin pour l'API
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Tag, BatchAnalysis


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin pour le modèle User personnalisé"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'company', 'analyses_count', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'company']
    ordering = ['-date_joined']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('company', 'bio', 'avatar')
        }),
        ('Statistiques', {
            'fields': ('analyses_count', 'api_calls_count'),
            'classes': ('collapse',)
        }),
        ('API', {
            'fields': ('api_key', 'api_key_created_at'),
            'classes': ('collapse',)
        }),
        ('Préférences', {
            'fields': ('email_notifications',)
        }),
    )
    
    readonly_fields = ['analyses_count', 'api_calls_count', 'api_key', 'api_key_created_at']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin pour les catégories"""
    list_display = ['name', 'slug', 'user', 'color', 'analyses_count', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    def analyses_count(self, obj):
        return obj.analyses.count()
    analyses_count.short_description = 'Analyses'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin pour les tags"""
    list_display = ['name', 'slug', 'user', 'color', 'created_at']
    list_filter = ['user', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']


@admin.register(BatchAnalysis)
class BatchAnalysisAdmin(admin.ModelAdmin):
    """Admin pour les analyses par lot"""
    list_display = ['id', 'name', 'user', 'status', 'total_pairs', 'processed_pairs', 'progress_percentage', 'created_at']
    list_filter = ['status', 'user', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    readonly_fields = ['progress_percentage', 'duration']
    
    def progress_percentage(self, obj):
        return f"{obj.progress_percentage}%"
    progress_percentage.short_description = 'Progression'
