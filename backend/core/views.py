from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, Case, When, Value, CharField
from django.utils import timezone
from datetime import timedelta
from .models import SeaArea, Farmer, Cage, CageFarmer
from .serializers import SeaAreaSerializer, FarmerSerializer, CageSerializer, CageFarmerSerializer


class DashboardStatsView(APIView):
    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        
        sea_areas = SeaArea.objects.count()
        cages = Cage.objects.count()
        farmers = Farmer.objects.count()
        
        pending_disease = DiseaseReport.objects.filter(status='pending').count()
        pending_mortality = MortalityReport.objects.filter(status='pending').count()
        pending_reports = pending_disease + pending_mortality
        
        abnormal_cages = Cage.objects.filter(status='abnormal').count()
        
        high_risk_areas = 0
        for area in SeaArea.objects.all():
            area_cages = area.cages.all()
            abnormal = area_cages.filter(
                Q(disease_reports__status='pending') |
                Q(mortality_reports__status='pending') |
                Q(status='abnormal')
            ).distinct().count()
            if abnormal >= 3:
                high_risk_areas += 1
        
        data = {
            'sea_areas': sea_areas,
            'cages': cages,
            'farmers': farmers,
            'pending_reports': pending_reports,
            'pending_disease': pending_disease,
            'pending_mortality': pending_mortality,
            'abnormal_cages': abnormal_cages,
            'high_risk_areas': high_risk_areas,
        }
        return Response(data)


class MonthlyTrendsView(APIView):
    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        trends = []
        now = timezone.now()
        
        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = now
            else:
                next_month = (now - timedelta(days=(i - 1) * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = next_month - timedelta(days=1)
            
            disease_count = DiseaseReport.objects.filter(
                report_time__gte=month_start,
                report_time__lte=month_end
            ).count()
            
            mortality_count = MortalityReport.objects.filter(
                report_time__gte=month_start,
                report_time__lte=month_end
            ).count()
            
            total_mortality = sum(
                r.mortality_count for r in MortalityReport.objects.filter(
                    report_time__gte=month_start,
                    report_time__lte=month_end
                )
            )
            
            trends.append({
                'month': month_start.strftime('%Y-%m'),
                'disease_reports': disease_count,
                'mortality_reports': mortality_count,
                'total_mortality': total_mortality,
            })
        
        return Response(trends)


class HeatmapDataView(APIView):
    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        data = []
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        for area in SeaArea.objects.all():
            cages = area.cages.all()
            cage_ids = cages.values_list('id', flat=True)
            
            disease_reports = DiseaseReport.objects.filter(
                cage_id__in=cage_ids,
                report_time__gte=seven_days_ago
            ).count()
            
            mortality_reports = MortalityReport.objects.filter(
                cage_id__in=cage_ids,
                report_time__gte=seven_days_ago
            ).count()
            
            abnormal_cages = cages.filter(
                Q(disease_reports__status='pending') |
                Q(mortality_reports__status='pending') |
                Q(status='abnormal')
            ).distinct().count()
            
            total_cages = cages.count()
            risk_score = 0
            if total_cages > 0:
                risk_score = (abnormal_cages / total_cages) * 50 + (disease_reports + mortality_reports) * 2
                risk_score = min(risk_score, 100)
            
            risk_level = 'low'
            if risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 20:
                risk_level = 'medium'
            
            data.append({
                'sea_area_id': area.id,
                'sea_area_name': area.name,
                'location': area.location,
                'lat': area.center_lat or 0,
                'lng': area.center_lng or 0,
                'total_cages': total_cages,
                'abnormal_cages': abnormal_cages,
                'disease_reports': disease_reports,
                'mortality_reports': mortality_reports,
                'risk_score': risk_score,
                'risk_level': risk_level,
            })
        
        return Response(data)


class FarmerResponsibilityView(APIView):
    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        data = []
        
        for farmer in Farmer.objects.all():
            cages = Cage.objects.filter(cage_farmers__farmer=farmer)
            cage_ids = cages.values_list('id', flat=True)
            
            disease_reports = DiseaseReport.objects.filter(cage_id__in=cage_ids).count()
            mortality_reports = MortalityReport.objects.filter(cage_id__in=cage_ids).count()
            
            pending_disease = DiseaseReport.objects.filter(
                cage_id__in=cage_ids, status='pending'
            ).count()
            
            pending_mortality = MortalityReport.objects.filter(
                cage_id__in=cage_ids, status='pending'
            ).count()
            
            anomaly_disease = DiseaseReport.objects.filter(
                cage_id__in=cage_ids, is_anomaly=True
            ).count()
            
            anomaly_mortality = MortalityReport.objects.filter(
                cage_id__in=cage_ids, is_anomaly=True
            ).count()
            
            total_mortality = sum(
                r.mortality_count for r in MortalityReport.objects.filter(cage_id__in=cage_ids)
            )
            
            data.append({
                'farmer_id': farmer.id,
                'farmer_name': farmer.name,
                'phone': farmer.phone,
                'sea_area': farmer.sea_area.name if farmer.sea_area else None,
                'cage_count': cages.count(),
                'disease_reports': disease_reports,
                'mortality_reports': mortality_reports,
                'pending_disease': pending_disease,
                'pending_mortality': pending_mortality,
                'anomaly_disease': anomaly_disease,
                'anomaly_mortality': anomaly_mortality,
                'total_mortality': total_mortality,
                'responsibility_score': pending_disease + pending_mortality + anomaly_disease + anomaly_mortality,
            })
        
        data.sort(key=lambda x: x['responsibility_score'], reverse=True)
        return Response(data)


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
        ).prefetch_related(
            'cages',
            'cages__cage_farmers',
            'cages__cage_farmers__farmer',
            'farmers'
        )
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return SeaAreaSerializer
        return SeaAreaSerializer

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
        farmer_id = self.request.query_params.get('farmer')
        if farmer_id:
            queryset = queryset.filter(cage_farmers__farmer_id=farmer_id)
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
        ).prefetch_related(
            'cage_farmers',
            'cage_farmers__farmer'
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



