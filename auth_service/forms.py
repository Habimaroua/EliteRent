from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

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
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'auth-input'})

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà enregistrée.")
        return email
