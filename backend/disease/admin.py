from django.contrib import admin
from .models import DiseaseReport, MortalityReport


@admin.register(DiseaseReport)
class DiseaseReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'cage', 'reporter', 'disease_type', 'severity', 'status', 'is_anomaly', 'report_time', 'created_at')
    list_filter = ('disease_type', 'severity', 'status', 'is_anomaly', 'report_time', 'created_at')
    search_fields = ('cage__code', 'reporter', 'description', 'treatment_method')
    ordering = ('-report_time',)
    readonly_fields = ('is_anomaly', 'anomaly_score')


@admin.register(MortalityReport)
class MortalityReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'cage', 'reporter', 'mortality_count', 'cause', 'status', 'is_anomaly', 'report_time', 'created_at')
    list_filter = ('cause', 'status', 'is_anomaly', 'report_time', 'created_at')
    search_fields = ('cage__code', 'reporter', 'description', 'treatment_method')
    ordering = ('-report_time',)
    readonly_fields = ('is_anomaly', 'anomaly_score')
