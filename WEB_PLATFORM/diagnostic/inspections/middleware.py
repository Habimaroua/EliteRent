from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class RoleRestrictionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_path = request.path
        
        # 1. Protection des routes Admin (/admin/*)
        if current_path.startswith('/admin/'):
            if not request.user.is_authenticated:
                return redirect('inspections:login')
            if not (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
                # Accès restreint -> Redirection vers Login
                messages.error(request, "Accès réservé aux administrateurs.")
                return redirect('inspections:login')

        # 2. Protection des routes Client (/client/*)
        if current_path.startswith('/client/'):
            if not request.user.is_authenticated:
                return redirect('inspections:login')
            # L'Admin peut accéder à tout, le client seulement à sa zone
            user_role = getattr(request.user.profile, 'role', None) if hasattr(request.user, 'profile') else None
            if user_role not in ['admin', 'client']:
                messages.error(request, "Veuillez vous connecter pour accéder à cet espace.")
                return redirect('inspections:login')

        # 3. Redirection auto si déjà connecté (Login/Register)
        if request.user.is_authenticated and current_path in [reverse('inspections:login'), reverse('inspections:register')]:
            if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
                return redirect('inspections:admin_dashboard')
            return redirect('inspections:dashboard')

        response = self.get_response(request)
        return response
