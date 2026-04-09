from django.contrib import admin
from .models import Car, Inspection, Booking, Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

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

@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'car', 'inspection_type', 'detections_count', 'created_at')
    list_filter = ('inspection_type', 'car', 'created_at')
    readonly_fields = ('created_at',)
