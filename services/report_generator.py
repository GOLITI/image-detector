"""
Service de génération de rapports PDF pour les analyses d'images
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    Image as RLImage, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from PIL import Image
import os


class ReportGenerator:
    """Génère des rapports PDF d'analyse de falsification d'images"""
    
    # Couleurs du thème
    PRIMARY_COLOR = colors.HexColor('#3B82F6')  # Bleu
    SUCCESS_COLOR = colors.HexColor('#22C55E')  # Vert
    WARNING_COLOR = colors.HexColor('#F59E0B')  # Orange
    ERROR_COLOR = colors.HexColor('#EF4444')    # Rouge
    GRAY_COLOR = colors.HexColor('#6B7280')     # Gris
    
    @staticmethod
    def get_verdict_color(verdict):
        """Retourne la couleur associée au verdict"""
        color_map = {
            'IDENTICAL': ReportGenerator.SUCCESS_COLOR,
            'VERY_SIMILAR': ReportGenerator.PRIMARY_COLOR,
            'SIMILAR': ReportGenerator.WARNING_COLOR,
            'DIFFERENT': ReportGenerator.ERROR_COLOR,
        }
        return color_map.get(verdict, ReportGenerator.GRAY_COLOR)
    
    @staticmethod
    def get_verdict_text(verdict):
        """Retourne le texte français du verdict"""
        text_map = {
            'IDENTICAL': 'IDENTIQUES',
            'VERY_SIMILAR': 'TRÈS SIMILAIRES',
            'SIMILAR': 'SIMILAIRES',
            'DIFFERENT': 'DIFFÉRENTES / FALSIFIÉES',
        }
        return text_map.get(verdict, 'INCONNU')
    
    @staticmethod
    def create_styles():
        """Crée les styles personnalisés pour le rapport"""
        styles = getSampleStyleSheet()
        
        # Titre principal
        styles.add(ParagraphStyle(
            name='MainTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=ReportGenerator.PRIMARY_COLOR,
        ))
        
        # Sous-titre
        styles.add(ParagraphStyle(
            name='SubTitle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=ReportGenerator.GRAY_COLOR,
        ))
        
        # Titre de section
        styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=15,
            spaceAfter=10,
            textColor=ReportGenerator.PRIMARY_COLOR,
            borderPadding=(0, 0, 5, 0),
        ))
        
        # Texte normal
        styles.add(ParagraphStyle(
            name='NormalText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
        ))
        
        # Texte de verdict
        styles.add(ParagraphStyle(
            name='VerdictText',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=10,
        ))
        
        # Hash style (monospace)
        styles.add(ParagraphStyle(
            name='HashText',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Courier',
            textColor=ReportGenerator.GRAY_COLOR,
        ))
        
        return styles
    
    @staticmethod
    def resize_image_for_report(image_path, max_width=7*cm, max_height=5*cm):
        """
        Redimensionne une image pour le rapport tout en gardant les proportions
        
        Args:
            image_path: Chemin vers l'image
            max_width: Largeur maximale
            max_height: Hauteur maximale
            
        Returns:
            tuple: (width, height) en unités ReportLab
        """
        try:
            with Image.open(image_path) as img:
                img_width, img_height = img.size
                
                # Calculer le ratio
                width_ratio = max_width / img_width
                height_ratio = max_height / img_height
                ratio = min(width_ratio, height_ratio)
                
                return img_width * ratio, img_height * ratio
        except Exception:
            return max_width, max_height
    
    @classmethod
    def generate_report(cls, analysis):
        """
        Génère un rapport PDF complet pour une analyse
        
        Args:
            analysis: Instance du modèle ImageAnalysis
            
        Returns:
            BytesIO: Buffer contenant le PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        styles = cls.create_styles()
        story = []
        
        # ===== EN-TÊTE =====
        story.append(Paragraph("🔍 RAPPORT D'ANALYSE DE FALSIFICATION", styles['MainTitle']))
        story.append(Paragraph(
            f"Analyse #{analysis.id} - Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            styles['SubTitle']
        ))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=cls.PRIMARY_COLOR))
        story.append(Spacer(1, 20))
        
        # ===== VERDICT PRINCIPAL =====
        verdict_color = cls.get_verdict_color(analysis.verdict)
        verdict_text = cls.get_verdict_text(analysis.verdict)
        
        story.append(Paragraph("VERDICT", styles['SectionTitle']))
        
        verdict_style = ParagraphStyle(
            'VerdictStyle',
            parent=styles['VerdictText'],
            textColor=verdict_color,
        )
        story.append(Paragraph(f"<b>{verdict_text}</b>", verdict_style))
        
        # Message du verdict
        verdict_messages = {
            'IDENTICAL': "Les images sont parfaitement identiques. Aucune modification détectée.",
            'VERY_SIMILAR': "Les images sont très similaires. Les différences peuvent être dues aux métadonnées ou à une compression différente.",
            'SIMILAR': "Les images présentent des similitudes mais avec quelques modifications visibles.",
            'DIFFERENT': "Les images sont significativement différentes. Falsification probable ou images complètement différentes.",
        }
        message = verdict_messages.get(analysis.verdict, "")
        story.append(Paragraph(message, styles['NormalText']))
        story.append(Spacer(1, 15))
        
        # ===== MÉTRIQUES =====
        story.append(Paragraph("📊 MÉTRIQUES D'ANALYSE", styles['SectionTitle']))
        
        metrics_data = [
            ['Métrique', 'Valeur', 'Interprétation'],
            ['Score SSIM', f"{analysis.ssim_score:.4f}", cls._get_ssim_interpretation(analysis.ssim_score)],
            ['Similarité', f"{analysis.similarity_percentage:.1f}%", 'Pourcentage de correspondance'],
            ['Durée d\'analyse', f"{analysis.analysis_duration}s", 'Temps de traitement'],
            ['Intégrité MD5', 'Identique' if analysis.md5_hash1 == analysis.md5_hash2 else 'Différent', 
             'Comparaison binaire'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[5*cm, 4*cm, 7*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cls.PRIMARY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.white),
            ('ROWHEIGHT', (0, 0), (-1, -1), 25),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 20))
        
        # ===== IMAGES ANALYSÉES =====
        story.append(Paragraph("🖼️ IMAGES ANALYSÉES", styles['SectionTitle']))
        
        # Créer un tableau avec les deux images côte à côte
        image_data = []
        
        try:
            img1_path = analysis.image1.path
            img2_path = analysis.image2.path
            
            img1_width, img1_height = cls.resize_image_for_report(img1_path)
            img2_width, img2_height = cls.resize_image_for_report(img2_path)
            
            img1 = RLImage(img1_path, width=img1_width, height=img1_height)
            img2 = RLImage(img2_path, width=img2_width, height=img2_height)
            
            image_data.append([img1, img2])
            image_data.append([
                Paragraph("<b>Image 1</b>", styles['NormalText']),
                Paragraph("<b>Image 2</b>", styles['NormalText'])
            ])
            
            images_table = Table(image_data, colWidths=[8*cm, 8*cm])
            images_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            story.append(images_table)
        except Exception as e:
            story.append(Paragraph(f"Impossible de charger les images: {str(e)}", styles['NormalText']))
        
        story.append(Spacer(1, 15))
        
        # ===== HASHES MD5 =====
        story.append(Paragraph("🔐 SIGNATURES NUMÉRIQUES (MD5)", styles['SectionTitle']))
        
        hash_data = [
            ['Image', 'Hash MD5'],
            ['Image 1', analysis.md5_hash1],
            ['Image 2', analysis.md5_hash2],
        ]
        
        hash_table = Table(hash_data, colWidths=[3*cm, 13*cm])
        hash_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), cls.GRAY_COLOR),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Courier'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E5E7EB')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9FAFB')),
            ('ROWHEIGHT', (0, 0), (-1, -1), 20),
        ]))
        story.append(hash_table)
        story.append(Spacer(1, 20))
        
        # ===== CARTE DE DIFFÉRENCE =====
        if analysis.difference_map:
            story.append(Paragraph("🗺️ CARTE DES DIFFÉRENCES", styles['SectionTitle']))
            story.append(Paragraph(
                "Cette carte thermique met en évidence les zones qui diffèrent entre les deux images. "
                "Les zones en rouge/jaune indiquent des différences significatives, tandis que les zones "
                "en bleu/vert représentent les parties similaires.",
                styles['NormalText']
            ))
            story.append(Spacer(1, 10))
            
            try:
                diff_path = analysis.difference_map.path
                diff_width, diff_height = cls.resize_image_for_report(
                    diff_path, max_width=14*cm, max_height=10*cm
                )
                diff_img = RLImage(diff_path, width=diff_width, height=diff_height)
                
                diff_table = Table([[diff_img]], colWidths=[16*cm])
                diff_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(diff_table)
            except Exception as e:
                story.append(Paragraph(f"Impossible de charger la carte: {str(e)}", styles['NormalText']))
            
            story.append(Spacer(1, 10))
            
            # Légende
            legend_data = [
                [
                    Paragraph('<font color="#3B82F6">■</font> Zones identiques', styles['NormalText']),
                    Paragraph('<font color="#F59E0B">■</font> Différences modérées', styles['NormalText']),
                    Paragraph('<font color="#EF4444">■</font> Différences importantes', styles['NormalText']),
                ]
            ]
            legend_table = Table(legend_data, colWidths=[5.3*cm, 5.3*cm, 5.3*cm])
            legend_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(legend_table)
        
        # ===== CARTE IA (si disponible) =====
        if hasattr(analysis, 'ai_difference_map') and analysis.ai_difference_map:
            story.append(PageBreak())
            story.append(Paragraph("🤖 ANALYSE PAR INTELLIGENCE ARTIFICIELLE", styles['SectionTitle']))
            story.append(Paragraph(
                "Cette carte a été générée par un modèle d'intelligence artificielle spécialisé dans "
                "la détection de manipulations d'images. Elle identifie les zones potentiellement "
                "retouchées ou falsifiées avec une précision accrue.",
                styles['NormalText']
            ))
            story.append(Spacer(1, 10))
            
            try:
                ai_path = analysis.ai_difference_map.path
                ai_width, ai_height = cls.resize_image_for_report(
                    ai_path, max_width=14*cm, max_height=10*cm
                )
                ai_img = RLImage(ai_path, width=ai_width, height=ai_height)
                
                ai_table = Table([[ai_img]], colWidths=[16*cm])
                ai_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                story.append(ai_table)
            except Exception:
                pass
            
            # Score IA si disponible
            if hasattr(analysis, 'ai_confidence_score') and analysis.ai_confidence_score:
                story.append(Spacer(1, 10))
                story.append(Paragraph(
                    f"<b>Score de confiance IA:</b> {analysis.ai_confidence_score:.1f}%",
                    styles['NormalText']
                ))
        
        story.append(Spacer(1, 30))
        
        # ===== FOOTER =====
        story.append(HRFlowable(width="100%", thickness=1, color=cls.GRAY_COLOR))
        story.append(Spacer(1, 10))
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=cls.GRAY_COLOR,
            alignment=TA_CENTER,
        )
        story.append(Paragraph(
            f"Rapport généré automatiquement par Image Detector | "
            f"Date d'analyse: {analysis.created_at.strftime('%d/%m/%Y %H:%M:%S')} | "
            f"ID: #{analysis.id}",
            footer_style
        ))
        story.append(Paragraph(
            "Ce rapport est fourni à titre informatif. Les résultats doivent être interprétés "
            "par un expert pour toute utilisation légale ou professionnelle.",
            footer_style
        ))
        
        # Construire le PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def _get_ssim_interpretation(ssim_score):
        """Retourne une interprétation du score SSIM"""
        if ssim_score >= 0.95:
            return "Excellente similarité"
        elif ssim_score >= 0.80:
            return "Bonne similarité"
        elif ssim_score >= 0.50:
            return "Similarité modérée"
        else:
            return "Faible similarité"
