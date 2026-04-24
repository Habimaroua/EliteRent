from django.urls import path
from . import views
from auth_service import views as auth_views

app_name = "inspections"

urlpatterns = [
    path("", views.home, name="home"),
    path("nos-vehicules/", views.car_fleet, name="car_fleet"),
    path("car/<int:pk>/", views.car_detail, name="car_detail"),
    path("car/<int:pk>/book/", views.book_car, name="book_car"),
    path("car/<int:car_id>/analyze/", views.upload_image, name="car_analyze"),
    path("car/<int:car_id>/compare/", views.compare_inspections, name="compare_inspections"),
    
    # Dashboards Duo
    path("client/dashboard/", views.client_dashboard, name="dashboard"),
    path("client/mes-locations/", views.client_bookings, name="client_bookings"),
    path("client/mes-dossiers/", views.client_reports, name="client_reports"),
    path("cockpit/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    path("upload/", views.upload_image, name="upload_image"),
    path("report/<int:pk>/", views.report_detail, name="report_detail"),
    # Authentification (Microservice Inscription)
    path('login/', auth_views.login_view, name='login'),
    path('register/', auth_views.register_view, name='register'),
    path('profile/', auth_views.profile_view, name='profile'),
    path('logout/', auth_views.logout_view, name='logout'),
    path("services/", views.services_view, name="services"),
    path("contact/", views.contact_view, name="contact"),
    path("innovation/", views.innovation_view, name="innovation"),
    path("client/inviter-un-ami/", views.invite_friend, name="invite_friend"),
    
    # Gestion des véhicules (CRUD ADMINE)
    path("cockpit/car-management/", views.car_management, name="car_management"),
    path("cockpit/car/add/", views.car_create, name="car_create"),
    path("cockpit/car/<int:pk>/edit/", views.car_edit, name="car_edit"),
    path("cockpit/car/<int:pk>/delete/", views.car_delete, name="car_delete"),
    
    # Gestion des réservations (ADMINE)
    path("cockpit/booking-management/", views.booking_management, name="booking_management"),
    path("cockpit/booking/<int:pk>/status/<str:status>/", views.booking_status_update, name="booking_status_update"),
    path("client/profile/", auth_views.profile_view, name="client_profile"),
    path("cockpit/ia-monitor/", views.ia_monitor, name="ia_monitor"),
    path("cockpit/users/", views.user_management, name="user_management"),
    path("cockpit/reports/", views.admin_reports, name="admin_reports"),
    path("cockpit/notifications/", views.admin_notifications, name="admin_notifications"),
    path("cockpit/settings/", views.admin_settings, name="admin_settings"),
    path("payment/<int:booking_id>/", views.payment_gate, name="payment_gate"),
    path("payment/process/", views.process_payment_gate, name="process_payment_gate"),
]
