import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image
import io


class ImageProcessor:
    """Service pour le traitement et la comparaison d'images"""

    @staticmethod
    def load_image_from_file(image_file):
        """
        Charge une image depuis un fichier Django UploadedFile

        Args:
            image_file: Fichier image uploadé

        Returns:
            numpy.ndarray: Image au format OpenCV (BGR)
        """
        # Lire le contenu du fichier
        image_file.seek(0)
        image_bytes = image_file.read()
        image_file.seek(0)

        # Convertir en array numpy
        nparr = np.frombuffer(image_bytes, np.uint8)

        # Décoder l'image
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return img

    @staticmethod
    def load_image_from_path(image_path):
        """
        Charge une image depuis un chemin de fichier

        Args:
            image_path (str): Chemin vers l'image

        Returns:
            numpy.ndarray: Image au format OpenCV (BGR)
        """
        img = cv2.imread(image_path)
        return img

    @staticmethod
    def resize_images_to_same_size(img1, img2):
        """
        Redimensionne deux images pour qu'elles aient la même taille

        Args:
            img1: Première image
            img2: Deuxième image

        Returns:
            tuple: (img1_resized, img2_resized)
        """
        # Obtenir les dimensions
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]

        # Utiliser la plus petite dimension commune
        target_height = min(h1, h2)
        target_width = min(w1, w2)

        # Redimensionner si nécessaire
        if (h1, w1) != (target_height, target_width):
            img1 = cv2.resize(img1, (target_width, target_height), interpolation=cv2.INTER_AREA)

        if (h2, w2) != (target_height, target_width):
            img2 = cv2.resize(img2, (target_width, target_height), interpolation=cv2.INTER_AREA)

        return img1, img2

    @staticmethod
    def calculate_ssim(img1, img2):
        """
        Calcule le score SSIM entre deux images

        Args:
            img1: Première image (BGR)
            img2: Deuxième image (BGR)

        Returns:
            tuple: (score_ssim, image_difference)
        """
        # Convertir en niveaux de gris
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Redimensionner si nécessaire
        if gray1.shape != gray2.shape:
            gray1, gray2 = ImageProcessor.resize_images_to_same_size(gray1, gray2)

        # Calculer SSIM
        score, diff = ssim(gray1, gray2, full=True)

        # Convertir la différence en format uint8
        diff = (diff * 255).astype("uint8")

        return score, diff

    @staticmethod
    def generate_difference_map(img1, img2, diff):
        """
        Génère une carte de différence avec couleurs simples sur l'image visible :
        - VERT semi-transparent = zones identiques
        - ROUGE semi-transparent = zones différentes
        L'image reste clairement visible en dessous.

        Args:
            img1: Première image
            img2: Deuxième image
            diff: Image de différence (niveaux de gris)

        Returns:
            numpy.ndarray: Image avec overlay de différences colorées
        """
        # Redimensionner les images si nécessaire
        img1_resized, img2_resized = ImageProcessor.resize_images_to_same_size(img1, img2)
        if diff.shape[:2] != img1_resized.shape[:2]:
            diff = cv2.resize(diff, (img1_resized.shape[1], img1_resized.shape[0]))
        
        # Créer une copie de l'image originale comme base
        result = img1_resized.copy()
        
        # Créer un overlay coloré
        overlay = img1_resized.copy()
        
        # Définir les seuils pour les différences
        # diff élevé = similaire (SSIM proche de 1), diff bas = différent
        threshold_identical = 200  # Très similaire
        threshold_different = 100  # Différent
        
        # Créer les masques
        mask_identical = diff >= threshold_identical
        mask_different = diff <= threshold_different
        mask_moderate = (diff > threshold_different) & (diff < threshold_identical)
        
        # Appliquer les couleurs (BGR format)
        # Vert pour les zones identiques
        overlay[mask_identical] = [0, 200, 0]  # Vert
        # Rouge pour les zones différentes  
        overlay[mask_different] = [0, 0, 220]  # Rouge
        # Orange pour les différences modérées
        overlay[mask_moderate] = [0, 165, 255]  # Orange
        
        # Fusionner avec l'image originale (30% overlay, 70% original)
        # Cela garde l'image bien visible tout en montrant les différences
        result = cv2.addWeighted(img1_resized, 0.7, overlay, 0.3, 0)
        
        return result

    @staticmethod
    def save_image_to_bytes(img, format='PNG'):
        """
        Convertit une image OpenCV en bytes pour sauvegarde Django

        Args:
            img: Image OpenCV
            format: Format de sortie (PNG, JPEG, etc.)

        Returns:
            io.BytesIO: Buffer contenant l'image
        """
        # Convertir BGR vers RGB pour PIL
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Créer une image PIL
        pil_img = Image.fromarray(img_rgb)

        # Sauvegarder dans un buffer
        buffer = io.BytesIO()
        pil_img.save(buffer, format=format)
        buffer.seek(0)

        return buffer

    @staticmethod
    def calculate_pixel_difference(img1, img2):
        """
        Calcule la différence pixel par pixel

        Args:
            img1: Première image
            img2: Deuxième image

        Returns:
            float: Pourcentage de différence
        """
        # Redimensionner si nécessaire
        if img1.shape != img2.shape:
            img1, img2 = ImageProcessor.resize_images_to_same_size(img1, img2)

        # Calculer la différence absolue
        diff = cv2.absdiff(img1, img2)

        # Compter les pixels différents
        diff_pixels = np.sum(diff > 0)
        total_pixels = diff.size

        # Calculer le pourcentage
        percentage = (diff_pixels / total_pixels) * 100

        return percentage