# EliteRent-AI : Diagnostic Carrosserie & Location Prestige

Système intelligent de gestion de flotte et de diagnostic automatique de carrosserie automobile par Intelligence Artificielle.

## Architecture

```
┌─────────────────┐     HTTP POST      ┌─────────────────┐
│  WEB_PLATFORM   │ ──────────────────► │   AI_SERVICE    │
│  (Django:8001)  │ ◄────────────────── │  (FastAPI:8000) │
│                 │   JSON + Base64     │  YOLOv8n-seg    │
└─────────────────┘                     └─────────────────┘
```

## Fonctionnalités Clés

- **Gestion de Flotte** : Catalogue de voitures premium avec suivi d'état.
- **Système de Réservation** : Formulaire complet avec capture d'identité client.
- **Diagnostic IA** : Détection automatique des dommages (rayures, bosses).
- **Comparaison Avant/Après** : Analyse différentielle lors de la restitution du véhicule.
- **Certificat de Santé** : Rapports détaillés et archivés pour chaque inspection.

## Lancement rapide

```bash
# Lancer les deux services simultanément (Windows)
.\start_all.ps1
```

- **Plateforme Web** : http://localhost:8001
- **API IA** : http://localhost:8000/docs

## Services

### AI_SERVICE (FastAPI - Port 8000)
- Modèle YOLOv8n-seg optimisé.
- Séparation entre éléments structurels et dommages réels.
- API REST pour les diagnostics en temps réel.

### WEB_PLATFORM (Django - Port 8001)
- Interface moderne "EliteRent" (Dark Mode / Glassmorphism).
- Gestion complète de la base de données (SQLite).
- Workflow de location : Réservation -> Départ -> Retour -> Comparaison.

## Note technique

Le système utilise YOLOv8 pour la segmentation. Pour une précision maximale en production sur des dommages spécifiques, un fine-tuning sur un dataset propriétaire de carrosserie est recommandé.
