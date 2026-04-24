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
    has_chauffeur = models.BooleanField(default=False, verbose_name="Chauffeur Privé (+150 DA/j)")
    has_insurance = models.BooleanField(default=False, verbose_name="Assurance Premium (+50 DA/j)")
    has_gps = models.BooleanField(default=False, verbose_name="Pack WiFi & GPS HP (+20 DA/j)")
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Réservation #{self.pk} - {self.customer_name} ({self.car})"
