import time
from django.core.files.base import ContentFile
from .hash_calculator import HashCalculator
from .image_processor import ImageProcessor
from .ai_detector import AIForgeryDetector


class ForgeryDetector:
    """Service principal pour la détection de falsification"""

    # Seuils de décision
    SSIM_THRESHOLD_VERY_SIMILAR = 0.95
    SSIM_THRESHOLD_SIMILAR = 0.80

    @staticmethod
    def analyze_images(analysis_instance):
        """
        Effectue l'analyse complète de deux images

        Args:
            analysis_instance: Instance du modèle ImageAnalysis avec image1 et image2

        Returns:
            ImageAnalysis: Instance mise à jour avec les résultats
        """
        start_time = time.time()

        try:
            # 1. Calculer les hashes MD5
            print("Calcul des hashes MD5...")
            analysis_instance.md5_hash1 = HashCalculator.calculate_md5(
                analysis_instance.image1.file
            )
            analysis_instance.md5_hash2 = HashCalculator.calculate_md5(
                analysis_instance.image2.file
            )

            # 2. Vérifier si les hashes sont identiques
            hashes_identical = HashCalculator.compare_hashes(
                analysis_instance.md5_hash1,
                analysis_instance.md5_hash2
            )

            if hashes_identical:
                # Images binaires identiques
                analysis_instance.verdict = 'IDENTICAL'
                analysis_instance.ssim_score = 1.0
                analysis_instance.similarity_percentage = 100.0
                print("Images identiques (MD5 identiques)")
            else:
                # 3. Charger les images avec OpenCV
                print("Chargement des images...")
                img1 = ImageProcessor.load_image_from_path(analysis_instance.image1.path)
                img2 = ImageProcessor.load_image_from_path(analysis_instance.image2.path)

                # 4. Redimensionner pour comparaison
                print("Redimensionnement des images...")
                img1_resized, img2_resized = ImageProcessor.resize_images_to_same_size(img1, img2)

                # 5. Calculer SSIM
                print("Calcul du score SSIM...")
                ssim_score, diff = ImageProcessor.calculate_ssim(img1_resized, img2_resized)
                analysis_instance.ssim_score = float(ssim_score)

                # 6. Calculer le pourcentage de similarité
                print("Calcul du pourcentage de similarité...")
                similarity_percentage = ssim_score * 100
                analysis_instance.similarity_percentage = float(similarity_percentage)

                # 7. Déterminer le verdict
                print("Détermination du verdict...")
                analysis_instance.verdict = ForgeryDetector._determine_verdict(ssim_score)

                # 8. Générer la carte de différence
                print("Génération de la carte de différence...")
                heatmap = ImageProcessor.generate_difference_map(
                    img1_resized,
                    img2_resized,
                    diff
                )

                # Sauvegarder la carte de différence
                heatmap_buffer = ImageProcessor.save_image_to_bytes(heatmap, format='PNG')
                analysis_instance.difference_map.save(
                    f'diff_map_{analysis_instance.id}.png',
                    ContentFile(heatmap_buffer.read()),
                    save=False
                )
                
                # 9. Analyse par Intelligence Artificielle
                print("Analyse IA des images...")
                try:
                    ai_detector = AIForgeryDetector()
                    ai_results = ai_detector.analyze_image_pair(
                        analysis_instance.image1.path,
                        analysis_instance.image2.path
                    )
                    
                    # Sauvegarder la carte IA
                    if 'visualization' in ai_results and ai_results['visualization'] is not None:
                        ai_map_buffer = ImageProcessor.save_image_to_bytes(
                            ai_results['visualization'], format='PNG'
                        )
                        analysis_instance.ai_difference_map.save(
                            f'ai_map_{analysis_instance.id}.png',
                            ContentFile(ai_map_buffer.read()),
                            save=False
                        )
                    
                    # Sauvegarder le score et les détails
                    analysis_instance.ai_confidence_score = ai_results.get('confidence_score', 0)
                    analysis_instance.ai_analysis_details = ai_results.get('details', {})
                    print(f"Analyse IA terminée - Score: {analysis_instance.ai_confidence_score:.2f}")
                except Exception as e:
                    print(f"Avertissement: Analyse IA échouée - {str(e)}")
                    # L'analyse continue sans l'IA

            # 10. Enregistrer la durée de l'analyse
            end_time = time.time()
            analysis_instance.analysis_duration = round(end_time - start_time, 2)

            print(f"Analyse terminée en {analysis_instance.analysis_duration}s")
            print(f"Verdict: {analysis_instance.get_verdict_display()}")

            return analysis_instance

        except Exception as e:
            print(f"Erreur lors de l'analyse: {str(e)}")
            raise

    @staticmethod
    def _determine_verdict(ssim_score):
        """
        Détermine le verdict basé sur le score SSIM

        Args:
            ssim_score (float): Score SSIM entre 0 et 1

        Returns:
            str: Verdict (VERY_SIMILAR, SIMILAR, ou DIFFERENT)
        """
        if ssim_score >= ForgeryDetector.SSIM_THRESHOLD_VERY_SIMILAR:
            return 'VERY_SIMILAR'
        elif ssim_score >= ForgeryDetector.SSIM_THRESHOLD_SIMILAR:
            return 'SIMILAR'
        else:
            return 'DIFFERENT'

    @staticmethod
    def get_verdict_message(verdict):
        """
        Retourne un message explicatif pour chaque verdict

        Args:
            verdict (str): Code du verdict

        Returns:
            str: Message explicatif
        """
        messages = {
            'IDENTICAL': "Les images sont parfaitement identiques. Aucune modification détectée.",
            'VERY_SIMILAR': "Les images sont très similaires. Les différences peuvent être dues aux métadonnées ou à une compression différente.",
            'SIMILAR': "Les images présentent des similitudes mais avec quelques modifications visibles.",
            'DIFFERENT': "Les images sont significativement différentes. Falsification probable ou images complètement différentes.",
        }
        return messages.get(verdict, "Verdict inconnu")