from django.contrib.auth.models import User
from inspections.models import Profile

def run():
    # 1. On cherche l'utilisateur admin@eliterent.com (ou on le crée)
    admin_email = "admin@eliterent.com"
    admin_pass = "admin123"
    
    # Nettoyage pré-existant si besoin (on veut qu'il soit unique)
    User.objects.filter(email=admin_email).delete()
    
    # Création du nouvel admin unique
    user = User.objects.create_user(username="admin", email=admin_email, password=admin_pass)
    user.is_staff = True
    user.is_superuser = True
    user.save()
    
    # S’assurer que son profil est bien ADMIN
    if hasattr(user, 'profile'):
        user.profile.role = 'admin'
        user.profile.save()
    else:
        Profile.objects.create(user=user, role='admin')
        
    # 2. Sécurité : On dégrade tous les AUTRES admins en clients
    others = User.objects.exclude(email=admin_email)
    for other in others:
        if hasattr(other, 'profile') and other.profile.role == 'admin':
            other.profile.role = 'client'
            other.profile.save()
            print(f"Rôle admin supprimé pour {other.email}")
            
    print(f"L'unique admin est maintenant : {admin_email}")

if __name__ == "__main__":
    run()
