"""
Serializers pour l'API REST
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.utils.text import slugify

from .models import User, Category, Tag, BatchAnalysis
from detector.models import ImageAnalysis


# ============================================
# USER SERIALIZERS
# ============================================

class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription d'un nouvel utilisateur"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'company']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer pour la connexion"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Identifiants invalides.")
        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé.")
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour les informations utilisateur"""
    analyses_count = serializers.IntegerField(read_only=True)
    api_calls_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'company', 'bio', 'avatar', 'analyses_count', 'api_calls_count',
            'email_notifications', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'analyses_count', 'api_calls_count', 'date_joined', 'last_login']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour du profil"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'company', 'bio', 'avatar', 'email_notifications']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value


class ApiKeySerializer(serializers.ModelSerializer):
    """Serializer pour la clé API"""
    class Meta:
        model = User
        fields = ['api_key', 'api_key_created_at']
        read_only_fields = ['api_key', 'api_key_created_at']


# ============================================
# CATEGORY & TAG SERIALIZERS
# ============================================

class TagSerializer(serializers.ModelSerializer):
    """Serializer pour les tags"""
    analyses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'analyses_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_analyses_count(self, obj):
        return obj.analyses.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


class CategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories"""
    analyses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'color', 'icon', 'analyses_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'analyses_count', 'created_at', 'updated_at']
    
    def get_analyses_count(self, obj):
        return obj.analyses.count()
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)


# ============================================
# IMAGE ANALYSIS SERIALIZERS
# ============================================

class ImageAnalysisListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des analyses"""
    verdict_display = serializers.CharField(source='get_verdict_display', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = ImageAnalysis
        fields = [
            'id', 'title', 'verdict', 'verdict_display', 'similarity_percentage',
            'ssim_score', 'category_name', 'tags', 'is_favorite', 'created_at',
            'analysis_duration'
        ]


class ImageAnalysisDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour le détail d'une analyse"""
    verdict_display = serializers.CharField(source='get_verdict_display', read_only=True)
    verdict_color = serializers.CharField(source='get_verdict_display_color', read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    user = UserSerializer(read_only=True)
    
    image1_url = serializers.SerializerMethodField()
    image2_url = serializers.SerializerMethodField()
    difference_map_url = serializers.SerializerMethodField()
    ai_difference_map_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImageAnalysis
        fields = [
            'id', 'title', 'notes', 'image1', 'image2', 'image1_url', 'image2_url',
            'md5_hash1', 'md5_hash2', 'ssim_score', 'similarity_percentage',
            'verdict', 'verdict_display', 'verdict_color',
            'difference_map', 'difference_map_url',
            'ai_difference_map', 'ai_difference_map_url', 'ai_confidence_score', 'ai_analysis_details',
            'category', 'tags', 'is_favorite', 'user',
            'created_at', 'analysis_duration'
        ]
    
    def get_image1_url(self, obj):
        request = self.context.get('request')
        if obj.image1 and request:
            return request.build_absolute_uri(obj.image1.url)
        return None
    
    def get_image2_url(self, obj):
        request = self.context.get('request')
        if obj.image2 and request:
            return request.build_absolute_uri(obj.image2.url)
        return None
    
    def get_difference_map_url(self, obj):
        request = self.context.get('request')
        if obj.difference_map and request:
            return request.build_absolute_uri(obj.difference_map.url)
        return None
    
    def get_ai_difference_map_url(self, obj):
        request = self.context.get('request')
        if obj.ai_difference_map and request:
            return request.build_absolute_uri(obj.ai_difference_map.url)
        return None


class ImageAnalysisCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une analyse"""
    image1 = serializers.ImageField(required=True)
    image2 = serializers.ImageField(required=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), required=False, default=[])
    
    class Meta:
        model = ImageAnalysis
        fields = ['image1', 'image2', 'title', 'notes', 'category_id', 'tag_ids']
    
    def validate_category_id(self, value):
        if value:
            user = self.context['request'].user
            if not Category.objects.filter(id=value, user=user).exists():
                raise serializers.ValidationError("Catégorie invalide.")
        return value
    
    def validate_tag_ids(self, value):
        if value:
            user = self.context['request'].user
            valid_tags = Tag.objects.filter(id__in=value, user=user).count()
            if valid_tags != len(value):
                raise serializers.ValidationError("Un ou plusieurs tags sont invalides.")
        return value


class ImageAnalysisUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour mettre à jour une analyse"""
    category_id = serializers.IntegerField(required=False, allow_null=True)
    tag_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    
    class Meta:
        model = ImageAnalysis
        fields = ['title', 'notes', 'category_id', 'tag_ids', 'is_favorite']
    
    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        tag_ids = validated_data.pop('tag_ids', None)
        
        if category_id is not None:
            instance.category_id = category_id
        
        if tag_ids is not None:
            instance.tags.set(tag_ids)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


# ============================================
# BATCH ANALYSIS SERIALIZERS
# ============================================

class BatchAnalysisListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des lots"""
    progress_percentage = serializers.FloatField(read_only=True)
    duration = serializers.FloatField(read_only=True)
    
    class Meta:
        model = BatchAnalysis
        fields = [
            'id', 'name', 'status', 'total_pairs', 'processed_pairs',
            'successful_pairs', 'failed_pairs', 'progress_percentage',
            'average_similarity', 'created_at', 'completed_at', 'duration'
        ]


class BatchAnalysisDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un lot"""
    analyses = ImageAnalysisListSerializer(many=True, read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    duration = serializers.FloatField(read_only=True)
    
    class Meta:
        model = BatchAnalysis
        fields = [
            'id', 'name', 'description', 'status', 'total_pairs', 'processed_pairs',
            'successful_pairs', 'failed_pairs', 'progress_percentage',
            'average_similarity', 'created_at', 'started_at', 'completed_at', 
            'duration', 'analyses'
        ]


class BatchImagePairSerializer(serializers.Serializer):
    """Serializer pour une paire d'images dans un lot"""
    image1 = serializers.ImageField()
    image2 = serializers.ImageField()
    title = serializers.CharField(required=False, max_length=200, default='')


class BatchAnalysisCreateSerializer(serializers.Serializer):
    """Serializer pour créer une analyse par lot"""
    name = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, default='')
    pairs = BatchImagePairSerializer(many=True, min_length=1, max_length=50)
    
    def validate_pairs(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Maximum 50 paires d'images par lot.")
        return value


# ============================================
# EXPORT SERIALIZERS
# ============================================

class ExportRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes d'export"""
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('json', 'JSON'),
    ]
    
    format = serializers.ChoiceField(choices=FORMAT_CHOICES, default='csv')
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    verdict = serializers.ChoiceField(choices=ImageAnalysis.VERDICT_CHOICES, required=False)
    category_id = serializers.IntegerField(required=False)
    include_images = serializers.BooleanField(default=False)


# ============================================
# STATISTICS SERIALIZERS
# ============================================

class UserStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques utilisateur"""
    total_analyses = serializers.IntegerField()
    analyses_this_month = serializers.IntegerField()
    analyses_this_week = serializers.IntegerField()
    
    verdict_distribution = serializers.DictField()
    average_similarity = serializers.FloatField()
    average_analysis_duration = serializers.FloatField()
    
    total_categories = serializers.IntegerField()
    total_tags = serializers.IntegerField()
    total_batches = serializers.IntegerField()
    
    most_used_category = serializers.CharField(allow_null=True)
    most_used_tags = serializers.ListField(child=serializers.CharField())
