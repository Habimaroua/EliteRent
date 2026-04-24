from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('client', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    
    def __str__(self):
        return f"Profil de {self.user.username} ({self.get_role_display()})"

@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """Gère la création du profil après la transaction pour éviter les erreurs de clé étrangère."""
    if created:
        # On utilise on_commit pour s'assurer que l'User existe bien en base avant de créer le profil
        # Cela règle les problèmes d'IntegrityError sur SQLite en multi-db
        def create_profile():
            Profile.objects.get_or_create(user=instance)
        
        transaction.on_commit(create_profile)
    else:
        # Pour les mises à jour
        try:
            instance.profile.save()
        except Exception:
            Profile.objects.get_or_create(user=instance)
