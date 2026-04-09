import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diagnostic.settings')
django.setup()

from inspections.models import Car

def update_images():
    print("Mise à jour des images de la flotte...")
    
    mapping = {
        ("Dacia", "Logan"): "cars/logan.png",
        ("Mercedes-Benz", "Classe G"): "cars/gclass.png",
        ("Volkswagen", "Golf 8"): "cars/golf8.png",
        ("Range Rover", "Vogue"): "cars/range.png",
    }
    
    for (brand, model), path in mapping.items():
        cars = Car.objects.filter(brand=brand, model_name=model)
        for car in cars:
            car.image = path
            car.save()
            print(f"Image mise à jour pour : {brand} {model}")
    
    print("--- Terminé ! ---")

if __name__ == "__main__":
    update_images()
