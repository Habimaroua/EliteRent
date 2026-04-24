from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'inspections', views.InspectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('run/', views.run_diagnostic_api, name='ia_diagnostic'),
]
