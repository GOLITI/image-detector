import os
from django.conf import settings


def cleanup_old_files(days=1):
    """
    Nettoie les fichiers uploadés de plus de X jours

    Args:
        days (int): Nombre de jours
    """
    import time
    from datetime import datetime, timedelta

    cutoff_date = datetime.now() - timedelta(days=days)
    cutoff_timestamp = time.mktime(cutoff_date.timetuple())

    # Dossiers à nettoyer
    folders = [
        os.path.join(settings.MEDIA_ROOT, 'uploads'),
        os.path.join(settings.MEDIA_ROOT, 'results'),
    ]

    deleted_count = 0

    for folder in folders:
        if os.path.exists(folder):
            for filename in os.listdir(folder):
                filepath = os.path.join(folder, filename)

                if os.path.isfile(filepath):
                    file_timestamp = os.path.getmtime(filepath)

                    if file_timestamp < cutoff_timestamp:
                        try:
                            os.remove(filepath)
                            deleted_count += 1
                        except Exception as e:
                            print(f"Erreur lors de la suppression de {filepath}: {e}")

    return deleted_count


def format_file_size(size_bytes):
    """
    Formate une taille de fichier en unités lisibles

    Args:
        size_bytes (int): Taille en bytes

    Returns:
        str: Taille formatée (ex: "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_verdict_badge_class(verdict):
    """
    Retourne la classe CSS DaisyUI pour un verdict

    Args:
        verdict (str): Code du verdict

    Returns:
        str: Classe CSS
    """
    classes = {
        'IDENTICAL': 'badge-success',
        'VERY_SIMILAR': 'badge-info',
        'SIMILAR': 'badge-warning',
        'DIFFERENT': 'badge-error',
    }
    return classes.get(verdict, 'badge-neutral')