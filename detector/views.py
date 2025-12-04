from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from .models import ImageAnalysis
from .forms import ImageUploadForm
from services.forgery_detector import ForgeryDetector
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
    analyses = ImageAnalysis.objects.all().order_by('-created_at')[:20]  # 20 dernières

    context = {
        'analyses': analyses,
        'page_title': 'Historique des analyses',
    }

    return render(request, 'detector/list.html', context)