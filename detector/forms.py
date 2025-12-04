from django import forms
from .models import ImageAnalysis
from utils.validators import validate_image_file, validate_image_dimensions


class ImageUploadForm(forms.ModelForm):
    """Formulaire pour l'upload de deux images"""

    class Meta:
        model = ImageAnalysis
        fields = ['image1', 'image2']
        widgets = {
            'image1': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/jpeg,image/png,image/bmp,image/tiff',
                'id': 'image1-input',
            }),
            'image2': forms.FileInput(attrs={
                'class': 'file-input file-input-bordered w-full',
                'accept': 'image/jpeg,image/png,image/bmp,image/tiff',
                'id': 'image2-input',
            }),
        }
        labels = {
            'image1': 'Première image',
            'image2': 'Deuxième image',
        }

    def clean_image1(self):
        """Valide la première image"""
        image1 = self.cleaned_data.get('image1')

        if image1:
            # Valider le type et la taille
            validate_image_file(image1)
            # Valider les dimensions
            validate_image_dimensions(image1)

        return image1

    def clean_image2(self):
        """Valide la deuxième image"""
        image2 = self.cleaned_data.get('image2')

        if image2:
            # Valider le type et la taille
            validate_image_file(image2)
            # Valider les dimensions
            validate_image_dimensions(image2)

        return image2

    def clean(self):
        """Validation globale du formulaire"""
        cleaned_data = super().clean()
        image1 = cleaned_data.get('image1')
        image2 = cleaned_data.get('image2')

        # Vérifier que les deux images sont présentes
        if not image1:
            raise forms.ValidationError("Veuillez sélectionner la première image.")

        if not image2:
            raise forms.ValidationError("Veuillez sélectionner la deuxième image.")

        return cleaned_data