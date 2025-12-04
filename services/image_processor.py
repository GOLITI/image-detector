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
        Génère une carte de différence colorée (heatmap)

        Args:
            img1: Première image
            img2: Deuxième image
            diff: Image de différence (niveaux de gris)

        Returns:
            numpy.ndarray: Carte de différence colorée
        """
        # Inverser la différence pour que les zones différentes soient plus claires
        diff_inverted = 255 - diff

        # Appliquer une colormap (rouge pour les différences)
        heatmap = cv2.applyColorMap(diff_inverted, cv2.COLORMAP_JET)

        # Fusionner avec l'image originale pour mieux voir
        # Utiliser la première image comme base
        img1_resized, _ = ImageProcessor.resize_images_to_same_size(img1, img2)

        # Superposer la heatmap (50% opacité)
        result = cv2.addWeighted(img1_resized, 0.5, heatmap, 0.5, 0)

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