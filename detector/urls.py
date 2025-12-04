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
]