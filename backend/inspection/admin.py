from django.contrib import admin
from .models import InspectionRoute, InspectionRouteCage, InspectionRecord, InspectionPoint


class InspectionRouteCageInline(admin.TabularInline):
    model = InspectionRouteCage
    extra = 1
    fields = ('cage', 'order')


@admin.register(InspectionRoute)
class InspectionRouteAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'creator', 'cage_count', 'created_at')
    list_filter = ('creator', 'created_at')
    search_fields = ('name', 'description', 'creator')
    ordering = ('-created_at',)
    inlines = [InspectionRouteCageInline]

    def cage_count(self, obj):
        return obj.cages.count()
    cage_count.short_description = '网箱数量'


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'route', 'inspector', 'status', 'start_time', 'end_time', 'created_at')
    list_filter = ('status', 'start_time', 'end_time', 'created_at')
    search_fields = ('route__name', 'inspector', 'remarks')
    ordering = ('-created_at',)


@admin.register(InspectionPoint)
class InspectionPointAdmin(admin.ModelAdmin):
    list_display = ('id', 'record', 'cage', 'check_time', 'water_temperature', 'ph_value', 'has_abnormality', 'created_at')
    list_filter = ('has_abnormality', 'water_quality', 'check_time', 'created_at')
    search_fields = ('cage__code', 'abnormal_condition')
    ordering = ('-check_time',)
