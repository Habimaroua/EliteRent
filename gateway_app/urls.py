from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('fleet/', views.car_fleet, name='car_fleet'),
    path('car/<int:pk>/', views.car_detail, name='car_detail'),
]
