from django.contrib import admin
from .models import Car, Booking

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model_name', 'license_plate', 'price_per_day', 'status')
    list_filter = ('status', 'brand')
    search_fields = ('brand', 'model_name', 'license_plate')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'car', 'start_date', 'duration_days', 'phone_number')
    list_filter = ('start_date', 'car')
    search_fields = ('customer_name', 'phone_number')
