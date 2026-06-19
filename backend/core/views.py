from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q, Case, When, Value, CharField
from .models import SeaArea, Farmer, Cage, CageFarmer
from .serializers import SeaAreaSerializer, FarmerSerializer, CageSerializer, CageFarmerSerializer


class SeaAreaViewSet(viewsets.ModelViewSet):
    queryset = SeaArea.objects.all()
    serializer_class = SeaAreaSerializer
    filterset_fields = ['name', 'location']
    search_fields = ['name', 'location', 'description']
    ordering_fields = ['created_at', 'name', 'area']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            cage_count=Count('cages', distinct=True),
            farmer_count=Count('farmers', distinct=True)
        )
        return queryset

    @action(detail=False, methods=['get'])
    def high_risk_areas(self, request):
        threshold = int(request.query_params.get('threshold', 3))
        queryset = self.get_queryset()
        high_risk_areas = []
        for area in queryset:
            abnormal_cages = area.cages.filter(
                Q(disease_reports__status='pending') |
                Q(mortality_reports__status='pending') |
                Q(status='abnormal')
            ).distinct().count()
            if abnormal_cages >= threshold:
                high_risk_areas.append({
                    'id': area.id,
                    'name': area.name,
                    'location': area.location,
                    'abnormal_cage_count': abnormal_cages,
                    'total_cages': area.cages.count(),
                    'risk_level': 'high' if abnormal_cages >= 5 else 'medium'
                })
        high_risk_areas.sort(key=lambda x: x['abnormal_cage_count'], reverse=True)
        return Response(high_risk_areas)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        area = self.get_object()
        cages = area.cages.all()
        total_capacity = sum(c.capacity for c in cages)
        status_stats = cages.values('status').annotate(count=Count('id'))
        farmers = area.farmers.all()
        data = {
            'id': area.id,
            'name': area.name,
            'total_cages': cages.count(),
            'total_farmers': farmers.count(),
            'total_capacity': total_capacity,
            'status_statistics': list(status_stats),
        }
        return Response(data)


class FarmerViewSet(viewsets.ModelViewSet):
    queryset = Farmer.objects.all()
    serializer_class = FarmerSerializer
    filterset_fields = ['name', 'phone', 'sea_area']
    search_fields = ['name', 'phone', 'id_card']
    ordering_fields = ['created_at', 'name', 'registration_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            cage_count=Count('cage_farmers', distinct=True)
        )
        return queryset

    @action(detail=True, methods=['get'])
    def cages(self, request, pk=None):
        farmer = self.get_object()
        cages = Cage.objects.filter(cage_farmers__farmer=farmer)
        serializer = CageSerializer(cages, many=True)
        return Response(serializer.data)


class CageViewSet(viewsets.ModelViewSet):
    queryset = Cage.objects.all()
    serializer_class = CageSerializer
    filterset_fields = ['code', 'sea_area', 'status', 'species']
    search_fields = ['code', 'location', 'species']
    ordering_fields = ['created_at', 'code', 'capacity', 'stocking_date']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            _abnormal_report_count=Count(
                'disease_reports',
                filter=Q(disease_reports__status='pending'),
                distinct=True
            ) + Count(
                'mortality_reports',
                filter=Q(mortality_reports__status='pending'),
                distinct=True
            )
        )
        queryset = queryset.annotate(
            is_high_risk=Q(_abnormal_report_count__gte=2) | Q(status='abnormal'),
            risk_level=Case(
                When(_abnormal_report_count__gte=5, then=Value('high')),
                When(_abnormal_report_count__gte=2, then=Value('medium')),
                When(status='abnormal', then=Value('medium')),
                default=Value('low'),
                output_field=CharField()
            )
        )
        return queryset

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        queryset = self.get_queryset()
        high_risk_cages = queryset.filter(is_high_risk=True)
        serializer = self.get_serializer(high_risk_cages, many=True)
        return Response({
            'count': high_risk_cages.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        status_stats = queryset.values('status').annotate(count=Count('id'))
        species_stats = queryset.values('species').annotate(count=Count('id')).exclude(species__isnull=True)
        high_risk_count = queryset.filter(is_high_risk=True).count()
        data = {
            'total_cages': total,
            'high_risk_count': high_risk_count,
            'status_statistics': list(status_stats),
            'species_statistics': list(species_stats),
        }
        return Response(data)

    @action(detail=True, methods=['get'])
    def farmers(self, request, pk=None):
        cage = self.get_object()
        farmers = Farmer.objects.filter(cage_farmers__cage=cage)
        serializer = FarmerSerializer(farmers, many=True)
        return Response(serializer.data)


class CageFarmerViewSet(viewsets.ModelViewSet):
    queryset = CageFarmer.objects.all()
    serializer_class = CageFarmerSerializer
    filterset_fields = ['cage', 'farmer']
    search_fields = ['cage__code', 'farmer__name']
    ordering_fields = ['created_at', 'start_date', 'end_date']



