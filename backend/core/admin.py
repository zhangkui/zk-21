from django.contrib import admin
from .models import SeaArea, Farmer, Cage, CageFarmer


@admin.register(SeaArea)
class SeaAreaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'area', 'depth', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'location', 'description')
    ordering = ('-created_at',)


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'id_card', 'sea_area', 'registration_date', 'created_at')
    list_filter = ('sea_area', 'registration_date', 'created_at')
    search_fields = ('name', 'phone', 'id_card')
    ordering = ('-created_at',)


@admin.register(Cage)
class CageAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'sea_area', 'location', 'capacity', 'species', 'status', 'created_at')
    list_filter = ('sea_area', 'status', 'stocking_date', 'created_at')
    search_fields = ('code', 'location', 'species')
    ordering = ('-created_at',)


@admin.register(CageFarmer)
class CageFarmerAdmin(admin.ModelAdmin):
    list_display = ('id', 'cage', 'farmer', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date', 'end_date', 'created_at')
    search_fields = ('cage__code', 'farmer__name')
    ordering = ('-created_at',)
