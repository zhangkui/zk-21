from rest_framework import serializers
from .models import SeaArea, Farmer, Cage, CageFarmer


class SeaAreaSerializer(serializers.ModelSerializer):
    cage_count = serializers.IntegerField(read_only=True)
    farmer_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SeaArea
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class FarmerSerializer(serializers.ModelSerializer):
    sea_area_name = serializers.CharField(source='sea_area.name', read_only=True)
    cage_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Farmer
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')


class CageSerializer(serializers.ModelSerializer):
    sea_area_name = serializers.CharField(source='sea_area.name', read_only=True)
    farmer_names = serializers.SerializerMethodField()
    is_high_risk = serializers.BooleanField(read_only=True)
    risk_level = serializers.CharField(read_only=True)

    class Meta:
        model = Cage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_farmer_names(self, obj):
        return [cf.farmer.name for cf in obj.cage_farmers.all()]


class CageFarmerSerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(source='cage.code', read_only=True)
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)

    class Meta:
        model = CageFarmer
        fields = '__all__'
        read_only_fields = ('created_at',)
