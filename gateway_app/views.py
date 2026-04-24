from django.shortcuts import render, get_object_or_404
from location_service.models import Car

def index(request):
    return render(request, 'inspections/index.html')

def car_fleet(request):
    cars = Car.objects.all()
    return render(request, 'inspections/car_fleet.html', {'cars': cars})

def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    return render(request, 'inspections/car_detail.html', {'car': car})
