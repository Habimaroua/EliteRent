from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Liaison Microservices (L'architecture que vous avez montrée)
    # Liaison Microservices et Interface
    path('', include('location_service.urls')),
    path('api/diagnostic/', include('diagnostic_service.urls')),
    path('api/payment/', include('payment_service.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
