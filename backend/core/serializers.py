from rest_framework import serializers
from .models import SeaArea, Farmer, Cage, CageFarmer


class FarmerSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farmer
        fields = ('id', 'name', 'phone')


class CageWithFarmerSerializer(serializers.ModelSerializer):
    sea_area_name = serializers.CharField(source='sea_area.name', read_only=True)
    farmer_names = serializers.SerializerMethodField()
    farmers = serializers.SerializerMethodField()
    is_high_risk = serializers.BooleanField(read_only=True)
    risk_level = serializers.CharField(read_only=True)

    class Meta:
        model = Cage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_farmer_names(self, obj):
        return [cf.farmer.name for cf in obj.cage_farmers.all()]

    def get_farmers(self, obj):
        return [
            {'id': cf.farmer.id, 'name': cf.farmer.name, 'phone': cf.farmer.phone}
            for cf in obj.cage_farmers.all()
        ]


class SeaAreaSerializer(serializers.ModelSerializer):
    cage_count = serializers.IntegerField(read_only=True)
    farmer_count = serializers.IntegerField(read_only=True)
    cages = CageWithFarmerSerializer(many=True, read_only=True)
    farmers = FarmerSimpleSerializer(many=True, read_only=True)
    center_lat = serializers.FloatField(read_only=True)
    center_lng = serializers.FloatField(read_only=True)

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
    farmers = serializers.SerializerMethodField()
    farmer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    is_high_risk = serializers.BooleanField(read_only=True)
    risk_level = serializers.CharField(read_only=True)

    class Meta:
        model = Cage
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_farmer_names(self, obj):
        return [cf.farmer.name for cf in obj.cage_farmers.all()]

    def get_farmers(self, obj):
        return [
            {'id': cf.farmer.id, 'name': cf.farmer.name, 'phone': cf.farmer.phone}
            for cf in obj.cage_farmers.all()
        ]

    def create(self, validated_data):
        farmer_ids = validated_data.pop('farmer_ids', [])
        cage = super().create(validated_data)
        if farmer_ids:
            for fid in farmer_ids:
                CageFarmer.objects.get_or_create(cage=cage, farmer_id=fid)
        return cage

    def update(self, instance, validated_data):
        farmer_ids = validated_data.pop('farmer_ids', None)
        cage = super().update(instance, validated_data)
        if farmer_ids is not None:
            existing_ids = set(cage.cage_farmers.values_list('farmer_id', flat=True))
            new_ids = set(farmer_ids)
            for remove_id in existing_ids - new_ids:
                CageFarmer.objects.filter(cage=cage, farmer_id=remove_id).delete()
            for add_id in new_ids - existing_ids:
                CageFarmer.objects.get_or_create(cage=cage, farmer_id=add_id)
        return cage


class CageFarmerSerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(source='cage.code', read_only=True)
    farmer_name = serializers.CharField(source='farmer.name', read_only=True)

    class Meta:
        model = CageFarmer
        fields = '__all__'
        read_only_fields = ('created_at',)
