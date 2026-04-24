from django.db import models

class Inspection(models.Model):
    INSPECTION_TYPES = [
        ('pickup', 'Départ (Prise en charge)'),
        ('return', 'Retour (Restitution)'),
    ]
    
    car_id = models.IntegerField(null=True, blank=True) # Référence à la voiture dans l'autre service
    inspection_type = models.CharField(max_length=10, choices=INSPECTION_TYPES, default='pickup')
    image_input = models.ImageField(upload_to="inputs/")
    image_output = models.ImageField(upload_to="outputs/", blank=True, null=True)
    result_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inspection #{self.pk} - Car ID {self.car_id}"
