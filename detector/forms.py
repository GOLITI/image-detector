from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import ImageAnalysis
from utils.validators import validate_image_file, validate_image_dimensions


User = get_user_model()


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


# ============================================
# AUTHENTICATION FORMS
# ============================================

class UserLoginForm(forms.Form):
    """Formulaire de connexion"""
    username = forms.CharField(
        label="Nom d'utilisateur ou email",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': "Nom d'utilisateur ou email",
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Mot de passe',
        })
    )
    remember_me = forms.BooleanField(
        label="Se souvenir de moi",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox checkbox-primary',
        })
    )


class UserRegistrationForm(forms.ModelForm):
    """Formulaire d'inscription"""
    password1 = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Mot de passe (min. 8 caractères)',
        }),
        validators=[validate_password],
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        widget=forms.PasswordInput(attrs={
            'class': 'input input-bordered w-full',
            'placeholder': 'Confirmez le mot de passe',
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': "Nom d'utilisateur",
                'autofocus': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Adresse email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Prénom',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nom',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Formulaire de modification du profil"""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'company']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Prénom',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nom',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Adresse email',
            }),
            'company': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Entreprise (optionnel)',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Vérifier l'unicité de l'email en excluant l'utilisateur actuel
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Cette adresse email est déjà utilisée.")
        return email