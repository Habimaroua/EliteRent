import os
import django
import random

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'diagnostic.settings')
django.setup()

from inspections.models import Car

cars_data = [
    ("Dacia", "Logan", 2023, "50 000DA/j", "La berline économique par excellence."),
    ("Dacia", "Sandero Stepway", 2022, "60 000DA/j", "Un look baroudeur pour la ville."),
    ("Renault", "Symbol", 2021, "45000 DA/j", "Confort et fiabilité."),
    ("Volkswagen", "Golf 8", 2023, "120 000 DA/j", "La référence des compactes."),
    ("Volkswagen", "Polo", 2022, "900000 DA/j", "Citadine dynamique et élégante."),
    ("Hyundai", "Tucson", 2023, "150 000 DA/j", "SUV moderne et spacieux."),
    ("Hyundai", "Accent", 2022, "70 000 DA/j", "Efficace et confortable."),
    ("Kia", "Sportage", 2023, "160 000 DA/j", "Design audacieux et grand confort."),
    ("Kia", "Picanto", 2022, "55 000 DA/j", "Parfaite pour la ville."),
    ("Seat", "Leon", 2023, "110000 DA/j", "Sportivité et technologie."),
    ("Seat", "Ibiza", 2022, "85 000DA/j", "Jeune et dynamique."),
    ("Mercedes-Benz", "Classe G", 2023, "500000 DA/j", "L'icône du luxe tout-terrain."),
    ("Mercedes-Benz", "Classe S", 2022, "450000 DA/j", "Le sommet de l'élégance."),
    ("Audi", "A3 Sportback", 2023, "130000 DA/j", "Compacte premium."),
    ("Audi", "Q5", 2022, "180000 DA/j", "Le SUV polyvalent de luxe."),
    ("Range Rover", "Vogue", 2023, "400000 DA/j", "Le raffinement ultime."),
    ("Peugeot", "208", 2023, "80000 DA/j", "Citadine au design futuriste."),
    ("Peugeot", "3008", 2022, "140000 DA/j", "Le SUV au i-Cockpit révolutionnaire."),
    ("Toyota", "Hilux", 2023, "150 000 DA/j", "La robustesse à toute épreuve."),
    ("Toyota", "Corolla", 2022, "950000 DA/j", "Hybride, efficace et durable.")
]

def populate():
    print("Début du peuplement de la flotte EliteRent...")
    count = 0
    for brand, model, year, price, desc in cars_data:
        # Générer une plaque d'immatriculation aléatoire unique (format algérien simplifié)
        plate = f"{random.randint(10000, 99999)}-{random.randint(100, 199)}-{random.randint(1, 48)}"
        
        # Vérifier si la plaque existe déjà (sécurité)
        if not Car.objects.filter(license_plate=plate).exists():
            car = Car.objects.create(
                brand=brand,
                model_name=model,
                year=year,
                license_plate=plate,
                price_per_day=float(price.split(' ')[0]),
                description=desc,
                status='excellent'
            )
            print(f"Ajouté : {brand} {model} ({plate})")
            count += 1
    
    print(f"--- Terminé ! {count} voitures ajoutées à la flotte. ---")

if __name__ == "__main__":
    populate()
