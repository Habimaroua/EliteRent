from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(allowed_roles=[]):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('inspections:login')
            
            if hasattr(request.user, 'profile') and request.user.profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            # Redirection si non autorisé vers login
            messages.error(request, "Accès restreint à votre type de profil.")
            return redirect('inspections:login')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required(allowed_roles=['admin'])(view_func)

def client_required(view_func):
    """Autorise Client ET Admin (puisqu'admin peut accéder à tout)."""
    return role_required(allowed_roles=['client', 'admin'])(view_func)
