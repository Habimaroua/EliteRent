from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import UserRegistrationForm, EmailLoginForm
from .models import Profile

def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie !")
            return redirect('inspections:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'inspections/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            # On cherche l'utilisateur par email d'abord
            try:
                user_obj = User.objects.get(email=email)
                username = user_obj.username
            except User.DoesNotExist:
                username = email # Fallback au cas où l'email soit le username
                
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Bon retour, {user.username} !")
                if hasattr(user, 'profile') and user.profile.role == 'admin':
                    return redirect('inspections:admin_dashboard')
                return redirect('inspections:dashboard')
            else:
                messages.error(request, "Email ou mot de passe invalide.")
    else:
        form = EmailLoginForm()
    return render(request, 'inspections/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('inspections:home')

def profile_view(request):
    if not request.user.is_authenticated:
        return redirect('inspections:login')
    profile = getattr(request.user, 'profile', None)
    return render(request, 'inspections/profile.html', {'profile': profile})
