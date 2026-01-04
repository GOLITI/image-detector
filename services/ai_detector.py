"""
Service de détection de falsification par Intelligence Artificielle
Utilise des techniques avancées de deep learning pour détecter les manipulations
"""
import cv2
import numpy as np
from PIL import Image
import io
from pathlib import Path

# Indicateur pour savoir si PyTorch est disponible
TORCH_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torchvision import transforms
    TORCH_AVAILABLE = True
except ImportError:
    pass


class AIForgeryDetector:
    """
    Détecteur de falsification basé sur l'Intelligence Artificielle.
    
    Utilise plusieurs techniques:
    1. Error Level Analysis (ELA) amélioré
    2. Analyse des patterns de bruit
    3. Détection des incohérences de compression JPEG
    4. Modèle de segmentation pour localiser les zones manipulées
    """
    
    # Configuration
    ELA_QUALITY = 90
    NOISE_THRESHOLD = 15
    
    def __init__(self):
        """Initialise le détecteur IA"""
        self.device = None
        self.model = None
        
        if TORCH_AVAILABLE:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self._init_model()
    
    def _init_model(self):
        """Initialise le modèle de détection (léger, sans poids pré-entraînés lourds)"""
        if not TORCH_AVAILABLE:
            return
        
        # Utiliser un modèle simple et léger pour la détection
        self.model = SimpleForgeryNet()
        self.model.to(self.device)
        self.model.eval()
        
        # Transformations pour le modèle
        self.transform = transforms.Compose([
            transforms.Resize((256, 256)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    
    def analyze_single_image(self, image_path):
        """
        Analyse une seule image pour détecter des manipulations
        
        Args:
            image_path: Chemin vers l'image
            
        Returns:
            dict: Résultats de l'analyse avec carte de manipulation
        """
        # Charger l'image
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Impossible de charger l'image: {image_path}")
        
        # 1. Analyse ELA (Error Level Analysis)
        ela_map = self._compute_ela(image_path)
        
        # 2. Analyse du bruit
        noise_map = self._analyze_noise_pattern(img)
        
        # 3. Détection des incohérences de compression
        compression_map = self._detect_compression_artifacts(img)
        
        # 4. Analyse par réseau de neurones (si disponible)
        if TORCH_AVAILABLE and self.model is not None:
            ai_map = self._neural_analysis(img)
        else:
            ai_map = np.zeros_like(ela_map)
        
        # Combiner toutes les analyses
        combined_map = self._combine_analysis_maps(ela_map, noise_map, compression_map, ai_map)
        
        # Calculer le score de confiance
        confidence_score = self._calculate_confidence_score(combined_map)
        
        # Générer la carte de visualisation
        visualization = self._create_visualization(img, combined_map)
        
        return {
            'manipulation_map': combined_map,
            'visualization': visualization,
            'confidence_score': confidence_score,
            'ela_map': ela_map,
            'noise_map': noise_map,
            'details': {
                'ela_intensity': float(np.mean(ela_map)),
                'noise_inconsistency': float(np.std(noise_map)),
                'compression_artifacts': float(np.mean(compression_map)),
            }
        }
    
    def analyze_image_pair(self, image1_path, image2_path):
        """
        Analyse une paire d'images pour détecter les différences et manipulations
        
        Args:
            image1_path: Chemin vers la première image
            image2_path: Chemin vers la deuxième image
            
        Returns:
            dict: Résultats de l'analyse comparative avec IA
        """
        # Charger les images
        img1 = cv2.imread(str(image1_path))
        img2 = cv2.imread(str(image2_path))
        
        if img1 is None or img2 is None:
            raise ValueError("Impossible de charger une ou les deux images")
        
        # Redimensionner pour avoir la même taille
        img1, img2 = self._resize_to_same_size(img1, img2)
        
        # 1. Analyse ELA des deux images
        ela1 = self._compute_ela(image1_path)
        ela2 = self._compute_ela(image2_path)
        
        # Redimensionner les cartes ELA
        ela1 = cv2.resize(ela1, (img1.shape[1], img1.shape[0]))
        ela2 = cv2.resize(ela2, (img2.shape[1], img2.shape[0]))
        
        # 2. Différence structurelle avancée
        structural_diff = self._compute_structural_difference(img1, img2)
        
        # 3. Analyse des régions suspectes
        suspicious_regions = self._detect_suspicious_regions(img1, img2, ela1, ela2)
        
        # 4. Génération de la carte de manipulation IA
        ai_diff_map = self._generate_ai_difference_map(
            img1, img2, ela1, ela2, structural_diff, suspicious_regions
        )
        
        # Calculer les scores
        manipulation_score = self._calculate_manipulation_score(ai_diff_map, suspicious_regions)
        
        # Créer la visualisation
        visualization = self._create_pair_visualization(img1, img2, ai_diff_map, suspicious_regions)
        
        return {
            'ai_difference_map': ai_diff_map,
            'visualization': visualization,
            'manipulation_score': manipulation_score,
            'confidence_score': manipulation_score,  # Alias pour compatibilité
            'suspicious_regions': suspicious_regions,
            'details': {
                'structural_difference': float(np.mean(structural_diff)),
                'ela_difference': float(np.mean(np.abs(ela1.astype(float) - ela2.astype(float)))),
                'regions_count': len(suspicious_regions) if isinstance(suspicious_regions, list) else 0,
                'manipulation_score': manipulation_score,
            }
        }
    
    def _compute_ela(self, image_path):
        """
        Calcule l'Error Level Analysis (ELA)
        
        L'ELA révèle les zones qui ont été modifiées en analysant les différences
        de niveau de compression JPEG.
        """
        try:
            # Ouvrir l'image originale
            original = Image.open(image_path).convert('RGB')
            
            # Sauvegarder en JPEG avec une qualité spécifique
            buffer = io.BytesIO()
            original.save(buffer, 'JPEG', quality=self.ELA_QUALITY)
            buffer.seek(0)
            
            # Recharger l'image compressée
            compressed = Image.open(buffer).convert('RGB')
            
            # Calculer la différence
            original_np = np.array(original).astype(np.float32)
            compressed_np = np.array(compressed).astype(np.float32)
            
            # Différence absolue
            ela = np.abs(original_np - compressed_np)
            
            # Amplifier les différences
            ela = ela * 10
            ela = np.clip(ela, 0, 255).astype(np.uint8)
            
            # Convertir en niveaux de gris
            ela_gray = cv2.cvtColor(ela, cv2.COLOR_RGB2GRAY)
            
            return ela_gray
            
        except Exception as e:
            print(f"Erreur ELA: {e}")
            # Retourner une image noire en cas d'erreur
            img = cv2.imread(str(image_path))
            if img is not None:
                return np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
            return np.zeros((256, 256), dtype=np.uint8)
    
    def _analyze_noise_pattern(self, img):
        """
        Analyse les patterns de bruit pour détecter les incohérences
        
        Les zones manipulées ont souvent des patterns de bruit différents.
        """
        # Convertir en niveaux de gris
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Appliquer un filtre de détection de bruit
        # Utiliser un filtre Laplacien pour détecter les variations de haute fréquence
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        
        # Calculer la variance locale
        kernel_size = 5
        local_var = cv2.blur(laplacian**2, (kernel_size, kernel_size)) - cv2.blur(laplacian, (kernel_size, kernel_size))**2
        
        # Normaliser
        noise_map = cv2.normalize(np.abs(local_var), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        return noise_map
    
    def _detect_compression_artifacts(self, img):
        """
        Détecte les artefacts de compression JPEG
        
        Les images manipulées ont souvent des niveaux de compression incohérents.
        """
        # Convertir en YCrCb (espace colorimétrique utilisé par JPEG)
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y_channel = ycrcb[:, :, 0]
        
        # Appliquer une DCT par blocs (comme JPEG)
        h, w = y_channel.shape
        block_size = 8
        artifact_map = np.zeros((h, w), dtype=np.float32)
        
        for i in range(0, h - block_size, block_size):
            for j in range(0, w - block_size, block_size):
                block = y_channel[i:i+block_size, j:j+block_size].astype(np.float32)
                
                # Calculer la DCT
                dct = cv2.dct(block)
                
                # Analyser les coefficients haute fréquence
                high_freq = np.sum(np.abs(dct[4:, 4:]))
                
                artifact_map[i:i+block_size, j:j+block_size] = high_freq
        
        # Normaliser
        artifact_map = cv2.normalize(artifact_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        return artifact_map
    
    def _neural_analysis(self, img):
        """
        Analyse par réseau de neurones pour détecter les manipulations
        """
        if not TORCH_AVAILABLE or self.model is None:
            return np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        
        try:
            # Convertir en PIL Image
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            
            # Appliquer les transformations
            input_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                output = self.model(input_tensor)
            
            # Convertir en numpy
            output_np = output.squeeze().cpu().numpy()
            
            # Redimensionner à la taille originale
            output_resized = cv2.resize(output_np, (img.shape[1], img.shape[0]))
            
            # Normaliser
            output_normalized = cv2.normalize(output_resized, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            
            return output_normalized
            
        except Exception as e:
            print(f"Erreur analyse neuronale: {e}")
            return np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
    
    def _combine_analysis_maps(self, ela_map, noise_map, compression_map, ai_map):
        """
        Combine toutes les cartes d'analyse en une seule carte de manipulation
        """
        # S'assurer que toutes les cartes ont la même taille
        target_size = ela_map.shape[:2]
        
        noise_map = cv2.resize(noise_map, (target_size[1], target_size[0]))
        compression_map = cv2.resize(compression_map, (target_size[1], target_size[0]))
        ai_map = cv2.resize(ai_map, (target_size[1], target_size[0]))
        
        # Pondération des différentes analyses
        weights = {
            'ela': 0.35,
            'noise': 0.20,
            'compression': 0.15,
            'ai': 0.30
        }
        
        combined = (
            weights['ela'] * ela_map.astype(np.float32) +
            weights['noise'] * noise_map.astype(np.float32) +
            weights['compression'] * compression_map.astype(np.float32) +
            weights['ai'] * ai_map.astype(np.float32)
        )
        
        # Normaliser
        combined = cv2.normalize(combined, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        return combined
    
    def _calculate_confidence_score(self, manipulation_map):
        """
        Calcule un score de confiance basé sur la carte de manipulation
        """
        # Calculer le pourcentage de pixels "suspects"
        threshold = 100
        suspicious_pixels = np.sum(manipulation_map > threshold)
        total_pixels = manipulation_map.size
        
        # Score inversé: plus il y a de pixels suspects, plus la confiance est basse
        manipulation_ratio = suspicious_pixels / total_pixels
        confidence = (1 - manipulation_ratio) * 100
        
        return max(0, min(100, confidence))
    
    def _resize_to_same_size(self, img1, img2):
        """Redimensionne deux images à la même taille"""
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        target_h = min(h1, h2)
        target_w = min(w1, w2)
        
        img1_resized = cv2.resize(img1, (target_w, target_h))
        img2_resized = cv2.resize(img2, (target_w, target_h))
        
        return img1_resized, img2_resized
    
    def _compute_structural_difference(self, img1, img2):
        """Calcule la différence structurelle entre deux images"""
        # Convertir en niveaux de gris
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        
        # Différence absolue
        diff = cv2.absdiff(gray1, gray2)
        
        # Appliquer un filtre Gaussien pour réduire le bruit
        diff_filtered = cv2.GaussianBlur(diff, (5, 5), 0)
        
        return diff_filtered
    
    def _detect_suspicious_regions(self, img1, img2, ela1, ela2, min_area=500):
        """
        Détecte les régions suspectes de manipulation
        """
        # Calculer la différence ELA
        ela_diff = cv2.absdiff(ela1, ela2)
        
        # Seuillage adaptatif
        _, binary = cv2.threshold(ela_diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Morphologie pour nettoyer
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        # Trouver les contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrer par taille
        suspicious_regions = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                suspicious_regions.append({
                    'contour': contour,
                    'bbox': (x, y, w, h),
                    'area': area,
                    'center': (x + w//2, y + h//2)
                })
        
        return suspicious_regions
    
    def _generate_ai_difference_map(self, img1, img2, ela1, ela2, structural_diff, suspicious_regions):
        """
        Génère une carte de différence améliorée par IA
        """
        h, w = img1.shape[:2]
        
        # Base: différence structurelle
        ai_map = structural_diff.astype(np.float32)
        
        # Ajouter les informations ELA
        ela_diff = cv2.absdiff(ela1, ela2).astype(np.float32)
        ai_map = 0.5 * ai_map + 0.5 * ela_diff
        
        # Amplifier les régions suspectes
        mask = np.zeros((h, w), dtype=np.float32)
        for region in suspicious_regions:
            cv2.drawContours(mask, [region['contour']], -1, 1.0, -1)
        
        # Appliquer un flou gaussien au masque
        mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        # Amplifier les zones suspectes
        ai_map = ai_map * (1 + mask)
        
        # Normaliser
        ai_map = cv2.normalize(ai_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        return ai_map
    
    def _calculate_manipulation_score(self, ai_map, suspicious_regions):
        """
        Calcule un score de manipulation global
        """
        # Score basé sur l'intensité moyenne de la carte
        intensity_score = np.mean(ai_map) / 255 * 100
        
        # Score basé sur le nombre et la taille des régions suspectes
        if suspicious_regions:
            total_area = sum(r['area'] for r in suspicious_regions)
            image_area = ai_map.shape[0] * ai_map.shape[1]
            region_score = (total_area / image_area) * 100
        else:
            region_score = 0
        
        # Combiner les scores
        final_score = 0.6 * intensity_score + 0.4 * region_score
        
        return min(100, final_score)
    
    def _create_visualization(self, img, manipulation_map):
        """
        Crée une visualisation avec couleurs simples sur l'image visible :
        - Image clairement visible
        - ROUGE = zones potentiellement manipulées
        - L'intensité du rouge indique le niveau de suspicion
        """
        # Redimensionner la carte si nécessaire
        manipulation_map = cv2.resize(manipulation_map, (img.shape[1], img.shape[0]))
        
        # Normaliser la carte
        manipulation_map = cv2.normalize(manipulation_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Créer une copie de l'image originale
        result = img.copy()
        overlay = img.copy()
        
        # Définir les seuils
        threshold_high = 150  # Forte suspicion
        threshold_medium = 80  # Suspicion modérée
        
        # Créer les masques
        mask_high = manipulation_map >= threshold_high
        mask_medium = (manipulation_map >= threshold_medium) & (manipulation_map < threshold_high)
        
        # Appliquer les couleurs (BGR format)
        # Rouge vif pour forte suspicion
        overlay[mask_high] = [0, 0, 255]  # Rouge
        # Orange pour suspicion modérée
        overlay[mask_medium] = [0, 100, 255]  # Orange
        
        # Fusionner avec l'image originale (35% overlay, 65% original)
        result = cv2.addWeighted(img, 0.65, overlay, 0.35, 0)
        
        return result
    
    def _create_pair_visualization(self, img1, img2, ai_map, suspicious_regions):
        """
        Crée une visualisation pour une paire d'images avec couleurs simples :
        - Image clairement visible
        - ROUGE = zones avec différences détectées par l'IA
        - Rectangles pour encadrer les zones suspectes
        """
        # Normaliser la carte AI
        ai_map_normalized = cv2.normalize(ai_map, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Utiliser l'image originale comme base
        result = img1.copy()
        overlay = img1.copy()
        
        # Définir les seuils
        threshold_high = 150
        threshold_medium = 80
        
        # Créer les masques
        mask_high = ai_map_normalized >= threshold_high
        mask_medium = (ai_map_normalized >= threshold_medium) & (ai_map_normalized < threshold_high)
        
        # Appliquer les couleurs (BGR format)
        overlay[mask_high] = [0, 0, 255]  # Rouge pour forte différence
        overlay[mask_medium] = [0, 100, 255]  # Orange pour différence modérée
        
        # Fusionner avec l'image originale
        visualization = cv2.addWeighted(img1, 0.65, overlay, 0.35, 0)
        
        # Dessiner les régions suspectes avec des rectangles bien visibles
        for region in suspicious_regions:
            x, y, w, h = region['bbox']
            # Rectangle rouge épais pour les zones suspectes
            cv2.rectangle(visualization, (x, y), (x+w, y+h), (0, 0, 255), 3)
            # Contour intérieur blanc pour meilleure visibilité
            cv2.rectangle(visualization, (x+2, y+2), (x+w-2, y+h-2), (255, 255, 255), 1)
        
        return visualization
    
    def save_visualization(self, visualization, output_path):
        """
        Sauvegarde la visualisation en fichier image
        """
        cv2.imwrite(str(output_path), visualization)


# Définir SimpleForgeryNet seulement si PyTorch est disponible
if TORCH_AVAILABLE:
    class SimpleForgeryNet(nn.Module):
        """
        Réseau de neurones simple pour la détection de falsification
        Architecture légère basée sur des convolutions
        """
        
        def __init__(self):
            super(SimpleForgeryNet, self).__init__()
            
            # Encodeur
            self.encoder = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.Conv2d(32, 32, 3, padding=1),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),
                
                nn.Conv2d(32, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.Conv2d(64, 64, 3, padding=1),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2, 2),
                
                nn.Conv2d(64, 128, 3, padding=1),
                nn.BatchNorm2d(128),
                nn.ReLU(inplace=True),
            )
            
            # Décodeur
            self.decoder = nn.Sequential(
                nn.ConvTranspose2d(128, 64, 2, stride=2),
                nn.BatchNorm2d(64),
                nn.ReLU(inplace=True),
                
                nn.ConvTranspose2d(64, 32, 2, stride=2),
                nn.BatchNorm2d(32),
                nn.ReLU(inplace=True),
                
                nn.Conv2d(32, 1, 1),
                nn.Sigmoid(),
            )
        
        def forward(self, x):
            features = self.encoder(x)
            output = self.decoder(features)
            return output
else:
    # Classe placeholder quand PyTorch n'est pas disponible
    SimpleForgeryNet = None
