from django.contrib import admin
from .models import ImageAnalysis


@admin.register(ImageAnalysis)
class ImageAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'verdict', 'ssim_score', 'similarity_percentage', 'created_at']
    list_filter = ['verdict', 'created_at']
    search_fields = ['md5_hash1', 'md5_hash2']
    readonly_fields = ['created_at', 'md5_hash1', 'md5_hash2', 'ssim_score',
                       'similarity_percentage', 'verdict', 'analysis_duration']

    fieldsets = (
        ('Images', {
            'fields': ('image1', 'image2')
        }),
        ('Hashes MD5', {
            'fields': ('md5_hash1', 'md5_hash2')
        }),
        ('Résultats', {
            'fields': ('verdict', 'ssim_score', 'similarity_percentage', 'difference_map')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'analysis_duration')
        }),
    )