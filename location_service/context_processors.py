from .models import Booking

def pending_bookings_count(request):
    """
    Rend le nombre de réservations en attente disponible dans tous les templates
    pour l'affichage des badges dans la sidebar.
    """
    if request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
        count = Booking.objects.filter(status='pending').count()
        return {'pending_count': count}
    return {'pending_count': 0}
