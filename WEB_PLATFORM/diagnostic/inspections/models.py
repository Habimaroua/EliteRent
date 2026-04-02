from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import json

class Car(models.Model):
    STATUS_CHOICES = [
        ('excellent', 'Excellent État'),
        ('good', 'Bon État'),
        ('damaged', 'Dommages Détectés'),
        ('maintenance', 'En Maintenance'),
    ]

    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    year = models.IntegerField()
    license_plate = models.CharField(max_length=20, unique=True)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="cars/", blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='excellent')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model_name} ({self.license_plate})"

    class Meta:
        ordering = ["-created_at"]

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings", null=True, blank=True)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="bookings")
    customer_name = models.CharField(max_length=200)
    start_date = models.DateField()
    duration_days = models.PositiveIntegerField(default=1)
    phone_number = models.CharField(max_length=20)
    id_card_photo = models.ImageField(upload_to="id_cards/")
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('validated', 'Validé'),
        ('cancelled', 'Annulé'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Options Premium
    has_chauffeur = models.BooleanField(default=False, verbose_name="Chauffeur Privé (+150€/j)")
    has_insurance = models.BooleanField(default=False, verbose_name="Assurance Premium (+50€/j)")
    has_gps = models.BooleanField(default=False, verbose_name="Pack WiFi & GPS HP (+20€/j)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réservation #{self.pk} - {self.customer_name} ({self.car})"

class Inspection(models.Model):
    INSPECTION_TYPES = [
        ('pickup', 'Départ (Prise en charge)'),
        ('return', 'Retour (Restitution)'),
    ]
    
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="inspections", null=True, blank=True)
    inspection_type = models.CharField(max_length=10, choices=INSPECTION_TYPES, default='pickup')
    image_input = models.ImageField(upload_to="inputs/")
    image_output = models.ImageField(upload_to="outputs/", blank=True, null=True)
    result_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        car_info = f" - {self.car}" if self.car else ""
        return f"Inspection #{self.pk}{car_info} - {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def detections_count(self):
        if self.result_json:
            return self.result_json.get("total_detections", 0)
        return 0

class Profile(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('client', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    
    def __str__(self):
        return f"Profil de {self.user.username} ({self.get_role_display()})"

# Signaux pour créer automatiquement un profil
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)
