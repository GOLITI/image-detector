from django.db import models
from django.utils import timezone
import os


def upload_to_image1(instance, filename):
    """Chemin pour l'upload de l'image 1"""
    ext = filename.split('.')[-1]
    filename = f"image1_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('uploads', filename)


def upload_to_image2(instance, filename):
    """Chemin pour l'upload de l'image 2"""
    ext = filename.split('.')[-1]
    filename = f"image2_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
    return os.path.join('uploads', filename)


def upload_to_difference_map(instance, filename):
    """Chemin pour la carte de différence"""
    filename = f"diff_map_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
    return os.path.join('results', filename)


class ImageAnalysis(models.Model):
    """Modèle pour stocker les analyses d'images"""

    VERDICT_CHOICES = [
        ('IDENTICAL', 'Identiques'),
        ('VERY_SIMILAR', 'Très similaires'),
        ('SIMILAR', 'Similaires'),
        ('DIFFERENT', 'Différentes/Falsifiées'),
    ]

    # Images uploadées
    image1 = models.ImageField(upload_to=upload_to_image1, verbose_name="Image 1")
    image2 = models.ImageField(upload_to=upload_to_image2, verbose_name="Image 2")

    # Hashes MD5
    md5_hash1 = models.CharField(max_length=32, verbose_name="Hash MD5 Image 1")
    md5_hash2 = models.CharField(max_length=32, verbose_name="Hash MD5 Image 2")

    # Résultats de l'analyse
    ssim_score = models.FloatField(null=True, blank=True, verbose_name="Score SSIM")
    similarity_percentage = models.FloatField(null=True, blank=True, verbose_name="Pourcentage de similarité")
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES, verbose_name="Verdict")

    # Carte de différence
    difference_map = models.ImageField(
        upload_to=upload_to_difference_map,
        null=True,
        blank=True,
        verbose_name="Carte des différences"
    )

    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    analysis_duration = models.FloatField(null=True, blank=True, verbose_name="Durée de l'analyse (s)")

    class Meta:
        verbose_name = "Analyse d'image"
        verbose_name_plural = "Analyses d'images"
        ordering = ['-created_at']

    def __str__(self):
        return f"Analyse #{self.id} - {self.verdict} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def get_verdict_display_color(self):
        """Retourne la couleur associée au verdict"""
        colors = {
            'IDENTICAL': 'success',
            'VERY_SIMILAR': 'info',
            'SIMILAR': 'warning',
            'DIFFERENT': 'error',
        }
        return colors.get(self.verdict, 'neutral')

    def get_verdict_icon(self):
        """Retourne l'icône associée au verdict"""
        icons = {
            'IDENTICAL': '✓',
            'VERY_SIMILAR': '≈',
            'SIMILAR': '⚠',
            'DIFFERENT': '✗',
        }
        return icons.get(self.verdict, '?')