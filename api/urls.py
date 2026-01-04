"""
URLs pour l'API REST
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from .views import (
    AuthViewSet, UserViewSet, CategoryViewSet, TagViewSet,
    ImageAnalysisViewSet, BatchAnalysisViewSet, ExportViewSet
)

# Router DRF
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'analyses', ImageAnalysisViewSet, basename='analysis')
router.register(r'batch', BatchAnalysisViewSet, basename='batch')
router.register(r'export', ExportViewSet, basename='export')

# URL patterns
urlpatterns = [
    # Auth endpoints
    path('auth/register/', AuthViewSet.as_view({'post': 'register'}), name='api-register'),
    path('auth/login/', AuthViewSet.as_view({'post': 'login'}), name='api-login'),
    path('auth/logout/', AuthViewSet.as_view({'post': 'logout'}), name='api-logout'),
    
    # Router URLs
    path('', include(router.urls)),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
