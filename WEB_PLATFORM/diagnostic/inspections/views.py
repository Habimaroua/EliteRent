import requests
import base64
from django.core.files.base import ContentFile

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q
from django.conf import settings
from .models import Car, Booking, Inspection
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import CarForm, BookingForm, EmailLoginForm, UserRegistrationForm
from django.contrib.admin.views.decorators import staff_member_required
from .decorators import admin_required, client_required

def home(request):
    """Page d'accueil de la plateforme (Vitrine sans la liste des véhicules)."""
    return render(request, "inspections/index.html")

def car_fleet(request):
    """Affiche la liste de tous les véhicules disponibles pour les clients."""
    cars = Car.objects.all()
    return render(request, "inspections/car_fleet.html", {"cars": cars})

def car_detail(request, pk):
    """Affiche les détails d'un véhicule spécifique."""
    car = get_object_or_404(Car, pk=pk)
    return render(request, "inspections/car_detail.html", {"car": car})

@client_required
def client_dashboard(request):
    """Tableau de bord : Résumé de l'activité du client."""
    if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
        return redirect("inspections:admin_dashboard")
        
    # On ne montre que les 3 dernières locations pour un aperçu rapide
    latest_bookings = Booking.objects.filter(user=request.user).order_by('-created_at')[:3]
    # Dernières inspections (3 max)
    inspections = Inspection.objects.filter(car__bookings__user=request.user).distinct().order_by('-created_at')[:3]
    
    return render(request, "inspections/client_dashboard.html", {
        "bookings": latest_bookings,
        "inspections": inspections,
        "total_bookings": Booking.objects.filter(user=request.user).count(),
        "loyalty_score": 1250, 
    })

@client_required
def client_bookings(request):
    """Historique complet des locations pour le client."""
    if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
        return redirect("inspections:admin_dashboard")
        
    status_filter = request.GET.get('status', '')
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
        
    return render(request, "inspections/client_bookings.html", {
        "bookings": bookings,
        "current_status": status_filter
    })

@client_required
def client_reports(request):
    """Historique complet des diagnostics IA (Dossiers Sécurité) pour le client."""
    if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
        return redirect("inspections:admin_dashboard")
        
    # On récupère toutes les inspections liées aux voitures que l'utilisateur a louées
    inspections = Inspection.objects.filter(car__bookings__user=request.user).distinct().order_by('-created_at')
    
    # Statistiques simples
    total_scans = inspections.count()
    
    return render(request, "inspections/client_reports.html", {
        "inspections": inspections,
        "total_scans": total_scans,
    })

@admin_required
def admin_dashboard(request):
    """Tableau de bord Cockpit pour l'Administrateur. Redirige le client s'il accède ici."""
    if hasattr(request.user, 'profile') and request.user.profile.role == 'client':
        return redirect("inspections:dashboard")
        
    bookings_pending = Booking.objects.filter(status='pending').order_by('-created_at')
    latest_inspections = Inspection.objects.all().order_by('-created_at')[:10]
    
    # Données pour les graphiques (Réel & JSON)
    import json
    from django.db.models import Count
    from django.db.models.functions import TruncMonth

    # 1. Graphique Locations par mois (Réel)
    months_labels = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
    monthly_data = [0] * 12
    monthly_qs = Booking.objects.values('created_at__month').annotate(count=Count('id'))
    for item in monthly_qs:
        m = item['created_at__month'] - 1
        if 0 <= m < 12:
            monthly_data[m] = item['count']

    # 2. Graphique État des véhicules
    status_map = {'excellent': 0, 'good': 0, 'damaged': 0, 'maintenance': 0}
    car_qs = Car.objects.values('status').annotate(count=Count('id'))
    for item in car_qs:
        status_map[item['status']] = item['count']
    
    status_data = [status_map['excellent'], status_map['good'], status_map['damaged'] + status_map['maintenance']]
    
    stats = {
        'total_cars': Car.objects.count(),
        'total_bookings': Booking.objects.count(),
        'pending_count': bookings_pending.count(),
        'total_inspections': Inspection.objects.count(),
        'total_users': User.objects.count(),
        'damaged_cars': Car.objects.filter(status='damaged').count(),
    }
    
    return render(request, "inspections/admin_dashboard.html", {
        "bookings_pending": bookings_pending,
        "latest_inspections": latest_inspections,
        "stats": stats,
        "monthly_data_json": json.dumps(monthly_data),
        "status_data_json": json.dumps(status_data)
    })

def upload_image(request, car_id=None):
    """Lancement du diagnostic IA (Accessible Administrateur & Client pour son véhicule)."""
    if not request.user.is_authenticated:
        return redirect('inspections:login')
        
    car = get_object_or_404(Car, id=car_id) if car_id else None
    inspection_type = request.GET.get('type', 'pickup')
    
    # Choix du template de base dynamique pour le sidebar
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
    base_template = "inspections/admin_base.html" if is_admin else "inspections/client_base.html"
    
    # Vérification de permission pour le client
    if not is_admin:
        if car:
            user_has_booked = Booking.objects.filter(user=request.user, car=car).exists()
            if not user_has_booked:
                messages.error(request, "Vous pouvez vérifier seulement la voiture que vous avez louée.")
                return redirect('inspections:dashboard')
        else:
            # Si pas de car_id, on regarde si l'utilisateur a une location
            user_bookings = Booking.objects.filter(user=request.user)
            if user_bookings.count() == 1:
                # Auto-sélection si unique
                return redirect('inspections:car_analyze', car_id=user_bookings.first().car.id)
            elif user_bookings.count() > 1:
                messages.info(request, "Choisissez le véhicule à scanner dans votre liste.")
                return redirect('inspections:client_bookings')
            else:
                messages.warning(request, "Vous n'avez pas de location enregistrée à scanner.")
                return redirect('inspections:dashboard')
    
    if request.method == "POST":
        image_file = request.FILES.get("image")
        inspection_type = request.POST.get("inspection_type", inspection_type)
        mileage = request.POST.get("mileage", "N/A")
        
        # Données de checklist manuelle
        manual_check = {
            "mileage": mileage,
            "pneus_ok": request.POST.get("pneus") == "on",
            "feux_ok": request.POST.get("feux") == "on",
            "proprete_ok": request.POST.get("proprete") == "on",
        }

        if image_file:
            inspection = Inspection.objects.create(
                car=car,
                image_input=image_file,
                inspection_type=inspection_type
            )
            
            # Initialiser result_json avec les données manuelles
            inspection.result_json = {"manual_check": manual_check}
            inspection.save()

            ai_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8000") + "/analyze"
            try:
                image_file.seek(0)
                files = {"image": (image_file.name, image_file.read(), image_file.content_type)}
                response = requests.post(ai_url, files=files, timeout=40)
                response.raise_for_status()
                data = response.json()

                inspection.result_json = data
                
                # Sauvegarder l'image annotée retournée par l'IA
                if "annotated_image_base64" in data:
                    img_data = base64.b64decode(data["annotated_image_base64"])
                    file_name = f"annotated_{inspection.pk}.jpg"
                    inspection.image_output.save(file_name, ContentFile(img_data), save=False)
                
                inspection.save()

                if car and data.get("damage_detected", False):
                    car.status = 'damaged'
                    car.save()

            except Exception as e:
                inspection.result_json = {"status": "error", "message": str(e)}
                inspection.save()
                messages.error(request, f"Problème avec la vérification : {str(e)}")
            
            # --- NOUVEAU : Calcul des différences avec la BDD si c'est le premier scan ---
            if car and car.image:
                try:
                    ai_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8000") + "/analyze"
                    with open(car.image.path, 'rb') as f:
                        files = {"image": (car.image.name, f.read(), "image/jpeg")}
                        ref_response = requests.post(ai_url, files=files, timeout=20)
                        if ref_response.status_code == 200:
                            ref_data = ref_response.json()
                            # On stocke aussi les détections de référence pour l'affichage
                            inspection.result_json['reference_detections'] = ref_data.get('detections', [])
                            inspection.save()
                except:
                    pass

            return redirect("inspections:report_detail", pk=inspection.pk)
        
    return render(request, "inspections/upload.html", {"car": car, "type": inspection_type, "base_template": base_template})

def report_detail(request, pk):
    """Affiche le rapport détaillé d'une inspection IA avec calcul des nouveaux dommages."""
    inspection = get_object_or_404(Inspection, pk=pk)
    
    # Récupération des détections actuelles
    detections = inspection.result_json.get('detections', [])
    total_damages = inspection.result_json.get('total_damages', 0)
    
    # On cherche une référence (BDD ou scan de départ)
    ref_dets = inspection.result_json.get('reference_detections', [])
    if not ref_dets:
        pickup = Inspection.objects.filter(car=inspection.car, inspection_type='pickup').exclude(pk=inspection.pk).first()
        if pickup:
            ref_dets = pickup.result_json.get('detections', [])
            
    # Marquage des nouveaux dommages
    processed_detections = []
    for det in detections:
        det_copy = det.copy()
        if det.get('is_damage'):
            is_new = True
            for r_det in ref_dets:
                if r_det.get('is_damage') and get_bbox_overlap(det['bbox'], r_det['bbox']) > 0.3:
                    is_new = False
                    break
            det_copy['is_new'] = is_new
        processed_detections.append(det_copy)

    health_score = max(0, 100 - (total_damages * 15))
    
    # Classification des dommages pour le rapport
    damage_summary = {}
    for det in processed_detections:
        if det.get('is_damage'):
            d_type = det.get('class', 'Autre')
            damage_summary[d_type] = damage_summary.get(d_type, 0) + 1
    
    base_template = "inspections/client_base.html"
    if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
        base_template = "inspections/admin_base.html"
    
    return render(request, "inspections/report_detail.html", {
        "inspection": inspection,
        "detections": processed_detections,
        "damage_summary": damage_summary,
        "health_score": health_score,
        "health_score_deg": health_score * 3.6,
        "base_template": base_template
    })

def get_bbox_overlap(box1, box2):
    """Calcule si deux boîtes englobantes se chevauchent suffisamment (IoU simplifié)."""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Intersection
    x_left = max(x1_1, x1_2)
    y_top = max(y1_1, y1_2)
    x_right = min(x2_1, x2_2)
    y_bottom = min(y2_1, y2_2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
        
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    
    return intersection_area / float(area1 + area2 - intersection_area)

@admin_required
def compare_inspections(request, car_id):
    """Compare une inspection avec soit le départ, soit la photo de référence de la BDD."""
    car = get_object_or_404(Car, id=car_id)
    
    # 1. On cherche la dernière inspection de retour
    return_insp = Inspection.objects.filter(car=car, inspection_type='return').order_by('-created_at').first()
    if not return_insp:
        # Si pas de retour, on montre juste le dernier scan existant
        return_insp = Inspection.objects.filter(car=car).order_by('-created_at').first()
    
    # 2. On cherche l'inspection de départ comme base
    pickup = Inspection.objects.filter(car=car, inspection_type='pickup').order_by('-created_at').first()
    
    base_detections = []
    comparison_source = "Scan de Départ"
    
    if pickup:
        base_detections = pickup.result_json.get('detections', [])
    elif car.image:
        # Si pas de scan de départ, on scanne la photo de la BDD à la volée
        comparison_source = "Photo Référence (BDD)"
        ai_url = getattr(settings, 'AI_SERVICE_URL', "http://localhost:8000") + "/analyze"
        try:
            with open(car.image.path, 'rb') as f:
                files = {"image": (car.image.name, f.read(), "image/jpeg")}
                response = requests.post(ai_url, files=files, timeout=10)
                if response.status_code == 200:
                    base_detections = response.json().get('detections', [])
        except Exception:
            pass

    differences = []
    if return_insp:
        return_dets = return_insp.result_json.get('detections', [])
        for r_det in return_dets:
            if not r_det.get('is_damage'): continue
            
            is_new = True
            for p_det in base_detections:
                if not p_det.get('is_damage'): continue
                if get_bbox_overlap(r_det['bbox'], p_det['bbox']) > 0.3:
                    is_new = False
                    break
            
            differences.append({
                'class': r_det.get('class', 'Dommage'),
                'confidence': r_det.get('confidence', 0),
                'status': 'NOUVEAU' if is_new else 'STABLE'
            })
            
    return render(request, "inspections/compare.html", {
        "car": car,
        "pickup": pickup,
        "return": return_insp,
        "differences": differences,
        "comparison_source": comparison_source
    })

def login_view(request):
    """Vue pour la connexion utilisateur par EMAIL avec redirection selon rôle."""
    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, "Connexion réussie. Bienvenue !")
                if hasattr(user, 'profile') and user.profile.role == 'admin':
                    return redirect("inspections:admin_dashboard")
                return redirect("inspections:dashboard")
            else:
                messages.error(request, "Email ou mot de passe incorrect.")
        else:
            messages.error(request, "Vérifiez vos informations.")
    else:
        form = EmailLoginForm()
    
    # Redirection auto si déjà connecté
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.role == 'admin':
            return redirect("inspections:admin_dashboard")
        return redirect("inspections:dashboard")
        
    return render(request, "inspections/login.html", {"form": form})

def register_view(request):
    """Vue pour l'inscription utilisateur avec EMAIL obligatoire."""
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, "Compte créé ! Bienvenue parmi nous.")
                return redirect("inspections:dashboard")
            except Exception:
                messages.error(request, "Désolé, il y a eu un problème lors de la création du compte.")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
    return render(request, "inspections/register.html", {"form": form})

def logout_view(request):
    """Vue pour la déconnexion. Redirige vers l'accueil public."""
    logout(request)
    messages.info(request, "C'est fini, vous avez quitté votre session.")
    return redirect("inspections:home")

def services_view(request):
    """Page présentant les services premium d'EliteRent-AI."""
    return render(request, "inspections/services.html")

def contact_view(request):
    """Page de contact avec formulaire et informations."""
    return render(request, "inspections/contact_page.html")

def innovation_view(request):
    """Page présentant les innovations technologiques YOLOv8."""
    return render(request, "inspections/innovation.html")

@client_required
def invite_friend(request):
    """Page de parrainage pour inviter des amis."""
    user_code = f"ELITE-{request.user.username[:3].upper()}-{request.user.id + 1000}"
    return render(request, "inspections/invite_friend.html", {
        "referral_code": user_code,
        "base_template": "inspections/client_base.html"
    })

# --- GESTION DES VÉHICULES (CRUD ADMIN) ---

@admin_required
def car_management(request):
    """Liste de tous les véhicules pour l'administration."""
    cars = Car.objects.all().order_by('-created_at')
    return render(request, "inspections/car_management.html", {"cars": cars})

@admin_required
def car_create(request):
    """Ajout d'un nouveau véhicule à la flotte."""
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Voiture ajoutée !")
            return redirect("inspections:car_management")
    else:
        form = CarForm()
    return render(request, "inspections/car_form.html", {"form": form, "title": "Ajouter un véhicule"})

@admin_required
def car_edit(request, pk):
    """Modification d'un véhicule existant."""
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            form.save()
            messages.success(request, f"{car.brand} {car.model_name} a été changé !")
            return redirect("inspections:car_management")
    else:
        form = CarForm(instance=car)
    return render(request, "inspections/car_form.html", {"form": form, "car": car, "title": f"Modifier {car.brand}"})

@admin_required
def car_delete(request, pk):
    """Suppression d'un véhicule."""
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        car.delete()
        messages.success(request, "Voiture retirée de la liste.")
        return redirect("inspections:car_management")
    return render(request, "inspections/car_confirm_delete.html", {"car": car})

# --- GESTION DES RÉSERVATIONS (ADMIN) ---

@admin_required
def booking_management(request):
    """Liste de toutes les réservations pour l'administration avec recherche et filtres."""
    query = request.GET.get('q', '').strip()
    client_id = request.GET.get('client', '')
    
    bookings = Booking.objects.all().select_related('user', 'car').order_by('-created_at')
    
    # Filtre par client spécifique
    if client_id:
        bookings = bookings.filter(user_id=client_id)
        
    # Recherche textuelle
    if query:
        bookings = bookings.filter(
            Q(customer_name__icontains=query) | 
            Q(car__brand__icontains=query) | 
            Q(car__model_name__icontains=query)
        )
        
    # Récupérer tous les utilisateurs qui ont des bookings pour le filtre
    # On utilise distinct pour avoir une liste propre
    clients = User.objects.filter(bookings__isnull=False).distinct()
    
    return render(request, "inspections/booking_management.html", {
        "bookings": bookings,
        "clients": clients,
        "current_query": query,
        "current_client": client_id
    })

@admin_required
def booking_status_update(request, pk, status):
    """Mise à jour rapide du statut d'une réservation depuis le Cockpit."""
    booking = get_object_or_404(Booking, pk=pk)
    if status in ['validated', 'cancelled', 'pending']:
        booking.status = status
        booking.save()
        messages.success(request, f"La location de {booking.customer_name} est maintenant : {booking.get_status_display()}")
    
    # Redirection intelligente : si on vient d'une page spécifique, on y retourne, sinon cockpit
    next_url = request.GET.get('next', 'inspections:admin_dashboard')
    return redirect(next_url)

def book_car(request, pk):
    """Création d'une réservation pour un véhicule spécifique (Côté Client)."""
    car = get_object_or_404(Car, pk=pk)
    if request.method == "POST":
        form = BookingForm(request.POST, request.FILES)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.car = car
            if request.user.is_authenticated:
                booking.user = request.user
                if not booking.customer_name:
                    booking.customer_name = request.user.username
            booking.save()
            messages.success(request, "Votre demande est envoyée ! Nous allons vous répondre très vite.")
            return redirect("inspections:dashboard")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = BookingForm()
    return render(request, "inspections/booking_form.html", {"form": form, "car": car})

@client_required
def profile_view(request):
    """Affiche et permet de gérer le profil utilisateur client."""
    return render(request, "inspections/profile.html")

@admin_required
def ia_monitor(request):
    """Moniteur global de tous les diagnostics IA de la flotte."""
    latest_inspections = Inspection.objects.all().order_by('-created_at')
    return render(request, "inspections/ia_monitor.html", {"latest_inspections": latest_inspections})

@admin_required
def user_management(request):
    """Gestion des comptes utilisateurs : Affiche exclusivement les clients par défaut."""
    # On force le filtre sur 'client' sauf si un autre rôle est explicitement demandé
    role_filter = request.GET.get('role', 'client')
    
    # On récupère uniquement les utilisateurs avec le rôle 'client' (ou le filtre spécifié)
    clients = User.objects.filter(profile__role=role_filter).select_related('profile').order_by('-date_joined')
    
    return render(request, "inspections/user_management.html", {
        "clients": clients,
        "current_role": role_filter
    })
@admin_required
def admin_reports(request):
    """Vue pour les rapports et analytics détaillés."""
    from django.db.models import Count
    
    popular_cars = Car.objects.annotate(booking_count=Count('bookings')).order_by('-booking_count')[:5]
    ai_stats = Inspection.objects.values('inspection_type').annotate(count=Count('id'))
    
    return render(request, "inspections/reports.html", {
        "popular_cars": popular_cars,
        "ai_stats": ai_stats
    })

@admin_required
def admin_notifications(request):
    """Vue pour les alertes et notifications système (Simulé)."""
    # Dans un vrai projet on utiliserait RabbitMQ/Celery
    # Ici on liste les événements récents du modèle
    recent_bookings = Booking.objects.all().order_by('-created_at')[:10]
    recent_inspections = Inspection.objects.all().order_by('-created_at')[:10]
    
    return render(request, "inspections/notifications.html", {
        "recent_bookings": recent_bookings,
        "recent_inspections": recent_inspections
    })

@admin_required
def admin_settings(request):
    """Vue pour les réglages du profil administrateur."""
    if request.method == "POST":
        # Logique de mise à jour simplifiée
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()
        messages.success(request, "Paramètres enregistrés.")
        
    return render(request, "inspections/settings.html")
