from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Car, Booking

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'brand', 'model_name', 'year', 'license_plate', 
            'price_per_day', 'status', 'description', 'image'
        ]
        widgets = {
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Marque'}),
            'model_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Modèle'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Année'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matricule'}),
            'price_per_day': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix par jour'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description du véhicule'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = [
            'customer_name', 'phone_number', 'start_date', 'duration_days', 
            'id_card_photo', 'has_chauffeur', 'has_insurance', 'has_gps'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-number-control', 'placeholder': '+213 ...'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de jours'}),
            'id_card_photo': forms.FileInput(attrs={'class': 'form-control'}),
            'has_chauffeur': forms.CheckboxInput(attrs={'class': 'premium-checkbox'}),
            'has_insurance': forms.CheckboxInput(attrs={'class': 'premium-checkbox'}),
            'has_gps': forms.CheckboxInput(attrs={'class': 'premium-checkbox'}),
        }

class EmailLoginForm(forms.Form):
    email = forms.EmailField(
        label="Adresse Email",
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'exemple@email.com', 'autocomplete': 'email'})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'auth-input', 'placeholder': '••••••••', 'autocomplete': 'current-password'})
    )

class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(
        label="Nom d'utilisateur / Pseudo",
        widget=forms.TextInput(attrs={'class': 'auth-input', 'placeholder': 'Ex: Jean Dupont'})
    )
    email = forms.EmailField(
        label="Adresse Email",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'auth-input', 'placeholder': 'votre@email.com'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # On injecte la classe CSS auth-input dans tous les champs générés par Django (dont les mots de passe)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'auth-input'})
            if 'password' in field.label.lower() or 'confirmation' in field.label.lower():
                field.widget.attrs.update({'placeholder': '••••••••'})

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà enregistrée.")
        return email
