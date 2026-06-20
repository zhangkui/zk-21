from rest_framework import serializers
from .models import InspectionRoute, InspectionRecord, InspectionPoint, InspectionRouteCage
from core.serializers import CageSerializer


class InspectionRouteCageSerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(source='cage.code', read_only=True)
    cage_details = CageSerializer(source='cage', read_only=True)

    class Meta:
        model = InspectionRouteCage
        fields = ('id', 'cage', 'cage_code', 'cage_details', 'order')


class InspectionRouteSerializer(serializers.ModelSerializer):
    cage_count = serializers.IntegerField(read_only=True)
    record_count = serializers.IntegerField(read_only=True)
    route_cages = InspectionRouteCageSerializer(source='inspectionroutecage_set', many=True, read_only=True)
    cage_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    creator_name = serializers.SerializerMethodField()

    class Meta:
        model = InspectionRoute
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'creator')

    def get_creator_name(self, obj):
        if obj.creator:
            full = obj.creator.get_full_name()
            return full if full else obj.creator.username
        return None

    def create(self, validated_data):
        cage_ids = validated_data.pop('cage_ids', [])
        route = InspectionRoute.objects.create(**validated_data)
        for idx, cage_id in enumerate(cage_ids):
            InspectionRouteCage.objects.create(
                route=route,
                cage_id=cage_id,
                order=idx
            )
        return route

    def update(self, instance, validated_data):
        cage_ids = validated_data.pop('cage_ids', None)
        instance = super().update(instance, validated_data)
        if cage_ids is not None:
            InspectionRouteCage.objects.filter(route=instance).delete()
            for idx, cage_id in enumerate(cage_ids):
                InspectionRouteCage.objects.create(
                    route=instance,
                    cage_id=cage_id,
                    order=idx
                )
        return instance


class InspectionPointSerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(source='cage.code', read_only=True)
    cage_details = CageSerializer(source='cage', read_only=True)

    class Meta:
        model = InspectionPoint
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'has_abnormality')


class InspectionRecordSerializer(serializers.ModelSerializer):
    route_name = serializers.CharField(source='route.name', read_only=True)
    point_count = serializers.IntegerField(read_only=True)
    abnormal_count = serializers.IntegerField(read_only=True)
    points = InspectionPointSerializer(many=True, read_only=True)
    point_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    inspector_name = serializers.SerializerMethodField()

    class Meta:
        model = InspectionRecord
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_inspector_name(self, obj):
        if obj.inspector:
            full = obj.inspector.get_full_name()
            return full if full else obj.inspector.username
        return '未分配'

    def create(self, validated_data):
        point_data_list = validated_data.pop('point_ids', [])
        record = InspectionRecord.objects.create(**validated_data)
        for point_data in point_data_list:
            if isinstance(point_data, dict):
                InspectionPoint.objects.create(record=record, **point_data)
        return record


class InspectionRecordDetailSerializer(serializers.ModelSerializer):
    route_name = serializers.CharField(source='route.name', read_only=True)
    point_count = serializers.IntegerField(read_only=True)
    abnormal_count = serializers.IntegerField(read_only=True)
    points = InspectionPointSerializer(many=True, read_only=True)
    route_details = InspectionRouteSerializer(source='route', read_only=True)
    inspector_name = serializers.SerializerMethodField()

    class Meta:
        model = InspectionRecord
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    def get_inspector_name(self, obj):
        if obj.inspector:
            full = obj.inspector.get_full_name()
            return full if full else obj.inspector.username
        return '未分配'
