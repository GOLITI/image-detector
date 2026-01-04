"""
Modèles pour l'API REST
Inclut le modèle utilisateur personnalisé, les tags et catégories
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import secrets


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec des champs supplémentaires
    """
    email = models.EmailField(unique=True, verbose_name="Email")
    company = models.CharField(max_length=100, blank=True, verbose_name="Entreprise")
    bio = models.TextField(blank=True, verbose_name="Biographie")
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    
    # Statistiques
    analyses_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'analyses")
    api_calls_count = models.PositiveIntegerField(default=0, verbose_name="Appels API")
    
    # API
    api_key = models.CharField(max_length=64, unique=True, blank=True, null=True, verbose_name="Clé API")
    api_key_created_at = models.DateTimeField(null=True, blank=True)
    
    # Préférences
    email_notifications = models.BooleanField(default=True, verbose_name="Notifications email")
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return self.username
    
    def generate_api_key(self):
        """Génère une nouvelle clé API"""
        self.api_key = secrets.token_hex(32)
        self.api_key_created_at = timezone.now()
        self.save(update_fields=['api_key', 'api_key_created_at'])
        return self.api_key
    
    def increment_analyses(self):
        """Incrémente le compteur d'analyses"""
        self.analyses_count += 1
        self.save(update_fields=['analyses_count'])
    
    def increment_api_calls(self):
        """Incrémente le compteur d'appels API"""
        self.api_calls_count += 1
        self.save(update_fields=['api_calls_count'])


class Category(models.Model):
    """
    Catégorie pour organiser les analyses
    """
    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, verbose_name="Slug")
    description = models.TextField(blank=True, verbose_name="Description")
    color = models.CharField(max_length=7, default="#3B82F6", verbose_name="Couleur")
    icon = models.CharField(max_length=50, default="folder", verbose_name="Icône")
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='categories',
        verbose_name="Propriétaire"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['name']
        unique_together = ['user', 'slug']
    
    def __str__(self):
        return self.name
    
    @property
    def analyses_count(self):
        return self.analyses.count()


class Tag(models.Model):
    """
    Tags pour étiqueter les analyses
    """
    name = models.CharField(max_length=50, verbose_name="Nom")
    slug = models.SlugField(verbose_name="Slug")
    color = models.CharField(max_length=7, default="#6B7280", verbose_name="Couleur")
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='tags',
        verbose_name="Propriétaire"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ['name']
        unique_together = ['user', 'slug']
    
    def __str__(self):
        return self.name


class BatchAnalysis(models.Model):
    """
    Analyse par lot de plusieurs paires d'images
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('FAILED', 'Échoué'),
        ('PARTIAL', 'Partiellement terminé'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nom du lot")
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name="Statut"
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='batch_analyses',
        verbose_name="Utilisateur"
    )
    
    # Statistiques
    total_pairs = models.PositiveIntegerField(default=0, verbose_name="Total de paires")
    processed_pairs = models.PositiveIntegerField(default=0, verbose_name="Paires traitées")
    successful_pairs = models.PositiveIntegerField(default=0, verbose_name="Réussies")
    failed_pairs = models.PositiveIntegerField(default=0, verbose_name="Échouées")
    
    # Temps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Résultats agrégés
    average_similarity = models.FloatField(null=True, blank=True, verbose_name="Similarité moyenne")
    
    class Meta:
        verbose_name = "Analyse par lot"
        verbose_name_plural = "Analyses par lot"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Lot #{self.id} - {self.name}"
    
    @property
    def progress_percentage(self):
        if self.total_pairs == 0:
            return 0
        return round((self.processed_pairs / self.total_pairs) * 100, 1)
    
    @property
    def duration(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def update_statistics(self):
        """Met à jour les statistiques du lot"""
        from detector.models import ImageAnalysis
        analyses = ImageAnalysis.objects.filter(batch=self)
        
        self.processed_pairs = analyses.count()
        self.successful_pairs = analyses.exclude(verdict__isnull=True).count()
        self.failed_pairs = analyses.filter(verdict__isnull=True).count()
        
        # Calcul de la similarité moyenne
        similarities = analyses.exclude(similarity_percentage__isnull=True).values_list('similarity_percentage', flat=True)
        if similarities:
            self.average_similarity = sum(similarities) / len(similarities)
        
        # Mise à jour du statut
        if self.processed_pairs == self.total_pairs:
            self.status = 'COMPLETED' if self.failed_pairs == 0 else 'PARTIAL'
            self.completed_at = timezone.now()
        
        self.save()
