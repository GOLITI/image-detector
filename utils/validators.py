from django.core.exceptions import ValidationError
import os


def validate_image_file(file):
    """
    Valide qu'un fichier est une image valide

    Args:
        file: Fichier uploadé

    Raises:
        ValidationError: Si le fichier n'est pas valide
    """
    # Vérifier l'extension
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    ext = os.path.splitext(file.name)[1].lower()

    if ext not in valid_extensions:
        raise ValidationError(
            f"Format de fichier non supporté. Formats acceptés: {', '.join(valid_extensions)}"
        )

    # Vérifier le type MIME
    valid_mime_types = [
        'image/jpeg',
        'image/png',
        'image/bmp',
        'image/tiff'
    ]

    if hasattr(file, 'content_type') and file.content_type not in valid_mime_types:
        raise ValidationError(
            "Le type de fichier n'est pas une image valide."
        )

    # Vérifier la taille (max 10 MB)
    max_size = 10 * 1024 * 1024  # 10 MB
    if file.size > max_size:
        raise ValidationError(
            f"Le fichier est trop volumineux. Taille maximale: 10 MB (Taille actuelle: {file.size / (1024 * 1024):.2f} MB)"
        )

    return True


def validate_image_dimensions(file, max_width=5000, max_height=5000):
    """
    Valide les dimensions d'une image

    Args:
        file: Fichier image
        max_width: Largeur maximale
        max_height: Hauteur maximale

    Raises:
        ValidationError: Si les dimensions sont trop grandes
    """
    from PIL import Image

    try:
        img = Image.open(file)
        width, height = img.size

        if width > max_width or height > max_height:
            raise ValidationError(
                f"Les dimensions de l'image sont trop grandes. Maximum: {max_width}x{max_height}px"
            )
    except Exception as e:
        raise ValidationError(f"Impossible de lire l'image: {str(e)}")

    return True