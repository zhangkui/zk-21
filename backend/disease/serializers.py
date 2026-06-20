from rest_framework import serializers
from .models import DiseaseReport, MortalityReport
from core.serializers import CageSerializer


def _user_display(user):
    if not user:
        return ''
    full = user.get_full_name()
    return full if full else user.username


class DiseaseReportSerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(source='cage.code', read_only=True)
    cage_details = CageSerializer(source='cage', read_only=True)
    disease_type_display = serializers.CharField(source='get_disease_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = DiseaseReport
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_anomaly', 'anomaly_score')

    def get_reporter_name(self, obj):
        return _user_display(obj.reporter)


class MortalityReportSerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(source='cage.code', read_only=True)
    cage_details = CageSerializer(source='cage', read_only=True)
    cause_display = serializers.CharField(source='get_cause_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    reporter_name = serializers.SerializerMethodField()

    class Meta:
        model = MortalityReport
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_anomaly', 'anomaly_score')

    def get_reporter_name(self, obj):
        return _user_display(obj.reporter)
