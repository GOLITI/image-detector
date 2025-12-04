import hashlib


class HashCalculator:
    """Service pour calculer le hash MD5 des images"""

    @staticmethod
    def calculate_md5(image_file):
        """
        Calcule le hash MD5 d'un fichier image

        Args:
            image_file: Fichier image (UploadedFile ou chemin)

        Returns:
            str: Hash MD5 en hexadécimal
        """
        md5_hash = hashlib.md5()

        # Si c'est un fichier uploadé Django
        if hasattr(image_file, 'read'):
            # Réinitialiser le pointeur au début du fichier
            image_file.seek(0)

            # Lire par chunks pour les gros fichiers
            for chunk in iter(lambda: image_file.read(4096), b""):
                md5_hash.update(chunk)

            # Réinitialiser le pointeur
            image_file.seek(0)
        else:
            # Si c'est un chemin de fichier
            with open(image_file, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)

        return md5_hash.hexdigest()

    @staticmethod
    def compare_hashes(hash1, hash2):
        """
        Compare deux hashes MD5

        Args:
            hash1 (str): Premier hash
            hash2 (str): Deuxième hash

        Returns:
            bool: True si identiques, False sinon
        """
        return hash1.lower() == hash2.lower()