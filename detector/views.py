from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ImageAnalysis
from .forms import ImageUploadForm, UserRegistrationForm, UserLoginForm, UserProfileForm
from services.forgery_detector import ForgeryDetector
from services.report_generator import ReportGenerator
import traceback


def index(request):
    """
    Vue principale - Page d'accueil avec formulaire d'upload
    """
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                # Créer l'instance sans sauvegarder
                analysis = form.save(commit=False)
                
                # Associer l'utilisateur si connecté
                if request.user.is_authenticated:
                    analysis.user = request.user

                # Sauvegarder pour obtenir un ID et les fichiers
                analysis.save()

                # Effectuer l'analyse
                analysis = ForgeryDetector.analyze_images(analysis)

                # Sauvegarder les résultats
                analysis.save()

                # Rediriger vers la page de résultats
                return redirect('detector:results', pk=analysis.id)

            except Exception as e:
                # En cas d'erreur, supprimer l'instance si elle existe
                if analysis.id:
                    analysis.delete()

                messages.error(
                    request,
                    f"Erreur lors de l'analyse des images : {str(e)}"
                )
                print(f"Erreur détaillée : {traceback.format_exc()}")
        else:
            # Afficher les erreurs de validation
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = ImageUploadForm()

    context = {
        'form': form,
        'page_title': 'Détecteur de Falsification d\'Images',
    }

    return render(request, 'detector/index.html', context)


def results(request, pk):
    """
    Vue des résultats d'analyse

    Args:
        pk: ID de l'analyse
    """
    analysis = get_object_or_404(ImageAnalysis, pk=pk)

    # Récupérer le message explicatif du verdict
    verdict_message = ForgeryDetector.get_verdict_message(analysis.verdict)

    context = {
        'analysis': analysis,
        'verdict_message': verdict_message,
        'page_title': f'Résultats de l\'analyse #{analysis.id}',
    }

    return render(request, 'detector/results.html', context)


@require_http_methods(["POST"])
def upload_ajax(request):
    """
    Vue AJAX pour l'upload et l'analyse d'images
    Retourne un JSON avec les résultats
    """
    try:
        form = ImageUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Créer et sauvegarder l'analyse
            analysis = form.save(commit=False)
            analysis.save()

            # Effectuer l'analyse
            analysis = ForgeryDetector.analyze_images(analysis)
            analysis.save()

            # Retourner les résultats en JSON
            return JsonResponse({
                'success': True,
                'analysis_id': analysis.id,
                'verdict': analysis.verdict,
                'verdict_display': analysis.get_verdict_display(),
                'verdict_message': ForgeryDetector.get_verdict_message(analysis.verdict),
                'md5_hash1': analysis.md5_hash1,
                'md5_hash2': analysis.md5_hash2,
                'ssim_score': analysis.ssim_score,
                'similarity_percentage': round(analysis.similarity_percentage, 2),
                'analysis_duration': analysis.analysis_duration,
                'difference_map_url': analysis.difference_map.url if analysis.difference_map else None,
                'image1_url': analysis.image1.url,
                'image2_url': analysis.image2.url,
            })
        else:
            # Retourner les erreurs
            errors = {}
            for field, error_list in form.errors.items():
                errors[field] = [str(error) for error in error_list]

            return JsonResponse({
                'success': False,
                'errors': errors,
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc(),
        }, status=500)


def delete_analysis(request, pk):
    """
    Supprime une analyse

    Args:
        pk: ID de l'analyse
    """
    if request.method == 'POST':
        analysis = get_object_or_404(ImageAnalysis, pk=pk)
        analysis.delete()
        messages.success(request, "L'analyse a été supprimée avec succès.")
        return redirect('detector:index')

    return redirect('detector:index')


def list_analyses(request):
    """
    Liste toutes les analyses effectuées
    """
    if request.user.is_authenticated:
        analyses = ImageAnalysis.objects.filter(user=request.user).order_by('-created_at')[:20]
    else:
        analyses = ImageAnalysis.objects.filter(user__isnull=True).order_by('-created_at')[:20]

    context = {
        'analyses': analyses,
        'page_title': 'Historique des analyses',
    }

    return render(request, 'detector/list.html', context)


def download_report(request, pk):
    """
    Génère et télécharge le rapport PDF d'une analyse
    
    Args:
        pk: ID de l'analyse
    """
    analysis = get_object_or_404(ImageAnalysis, pk=pk)
    
    try:
        # Générer le rapport PDF
        pdf_buffer = ReportGenerator.generate_report(analysis)
        
        # Préparer la réponse HTTP
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="rapport_analyse_{analysis.id}.pdf"'
        
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du rapport: {str(e)}")
        return redirect('detector:results', pk=pk)


# ============================================
# AUTHENTICATION VIEWS
# ============================================

def user_login(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('detector:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Bienvenue, {user.first_name or user.username} !")
                
                # Rediriger vers la page demandée ou le dashboard
                next_url = request.GET.get('next', 'detector:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    else:
        form = UserLoginForm()
    
    return render(request, 'detector/auth/login.html', {'form': form})


def user_register(request):
    """Vue d'inscription"""
    if request.user.is_authenticated:
        return redirect('detector:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Votre compte a été créé avec succès !")
            return redirect('detector:dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'detector/auth/register.html', {'form': form})


def user_logout(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('detector:index')


@login_required
def dashboard(request):
    """Tableau de bord personnel"""
    user = request.user
    now = timezone.now()
    
    # Récupérer les analyses de l'utilisateur
    user_analyses = ImageAnalysis.objects.filter(user=user)
    
    # Statistiques
    stats = {
        'total_analyses': user_analyses.count(),
        'identical_count': user_analyses.filter(verdict='IDENTICAL').count(),
        'similar_count': user_analyses.filter(verdict__in=['VERY_SIMILAR', 'SIMILAR']).count(),
        'different_count': user_analyses.filter(verdict='DIFFERENT').count(),
        'avg_similarity': user_analyses.aggregate(avg=Avg('similarity_percentage'))['avg'] or 0,
        'this_month': user_analyses.filter(created_at__gte=now - timedelta(days=30)).count(),
        'this_week': user_analyses.filter(created_at__gte=now - timedelta(days=7)).count(),
    }
    
    # Analyses récentes
    recent_analyses = user_analyses.order_by('-created_at')[:10]
    
    # Favoris
    favorite_analyses = user_analyses.filter(is_favorite=True).order_by('-created_at')[:6]
    
    # Catégories
    categories = []
    if hasattr(user, 'categories'):
        categories = user.categories.annotate(analyses_count=Count('analyses')).order_by('-analyses_count')[:5]
    
    context = {
        'stats': stats,
        'recent_analyses': recent_analyses,
        'favorite_analyses': favorite_analyses,
        'categories': categories,
        'page_title': 'Tableau de bord',
    }
    
    return render(request, 'detector/dashboard.html', context)


@login_required
def profile(request):
    """Vue du profil utilisateur"""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès !")
            return redirect('detector:profile')
    else:
        form = UserProfileForm(instance=user)
    
    # Statistiques
    stats = {
        'total_analyses': ImageAnalysis.objects.filter(user=user).count(),
    }
    
    context = {
        'form': form,
        'stats': stats,
        'page_title': 'Mon profil',
    }
    
    return render(request, 'detector/auth/profile.html', context)


@login_required
def change_password(request):
    """Changement de mot de passe"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        if not request.user.check_password(old_password):
            messages.error(request, "Mot de passe actuel incorrect.")
        elif new_password1 != new_password2:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
        elif len(new_password1) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Mot de passe modifié avec succès !")
    
    return redirect('detector:profile')


@login_required
def generate_api_key(request):
    """Générer une nouvelle clé API"""
    if request.method == 'POST':
        request.user.generate_api_key()
        messages.success(request, "Nouvelle clé API générée avec succès !")
    return redirect('detector:profile')


@login_required
@require_http_methods(["POST"])
def toggle_favorite(request, pk):
    """Ajouter/retirer une analyse des favoris"""
    analysis = get_object_or_404(ImageAnalysis, pk=pk, user=request.user)
    analysis.is_favorite = not analysis.is_favorite
    analysis.save(update_fields=['is_favorite'])
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'is_favorite': analysis.is_favorite})
    
    messages.success(request, "Favori mis à jour !")
    return redirect('detector:results', pk=pk)