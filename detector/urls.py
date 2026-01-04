from django.urls import path
from . import views

app_name = 'detector'

urlpatterns = [
    # Page principale
    path('', views.index, name='index'),

    # Résultats d'analyse
    path('results/<int:pk>/', views.results, name='results'),

    # Upload AJAX (optionnel)
    path('api/upload/', views.upload_ajax, name='upload_ajax'),

    # Suppression d'analyse
    path('delete/<int:pk>/', views.delete_analysis, name='delete'),

    # Liste des analyses
    path('history/', views.list_analyses, name='history'),
    
    # Téléchargement du rapport PDF
    path('report/<int:pk>/download/', views.download_report, name='download_report'),
    
    # ============================================
    # AUTHENTICATION URLS
    # ============================================
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('generate-api-key/', views.generate_api_key, name='generate_api_key'),
    
    # Favoris
    path('analysis/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),
]