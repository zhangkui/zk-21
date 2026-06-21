from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Case, When, Value, CharField, Sum
from django.utils import timezone
from datetime import timedelta
from .models import SeaArea, Farmer, Cage, CageFarmer
from .serializers import SeaAreaSerializer, FarmerSerializer, CageSerializer, CageFarmerSerializer
from accounts.permissions import (
    IsAdminUser,
    role_permission,
    is_admin,
    is_farmer,
    get_user_farmer,
    get_farmer_cage_ids,
    get_role_code,
)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport

        user = request.user
        farmer = get_user_farmer(user) if is_farmer(user) else None
        cage_ids = None
        if is_farmer(user) and farmer:
            cage_ids = list(Cage.objects.filter(cage_farmers__farmer=farmer).values_list('id', flat=True))

        if cage_ids is not None:
            cages_qs = Cage.objects.filter(id__in=cage_ids)
            sea_areas_qs = SeaArea.objects.filter(cages__in=cages_qs).distinct()
            farmers_qs = Farmer.objects.filter(pk=farmer.pk) if farmer else Farmer.objects.none()
        else:
            cages_qs = Cage.objects.all()
            sea_areas_qs = SeaArea.objects.all()
            farmers_qs = Farmer.objects.all()

        sea_areas = sea_areas_qs.count()
        cages = cages_qs.count()
        farmers = farmers_qs.count()

        disease_qs = DiseaseReport.objects.all()
        mortality_qs = MortalityReport.objects.all()
        if cage_ids is not None:
            disease_qs = disease_qs.filter(cage_id__in=cage_ids)
            mortality_qs = mortality_qs.filter(cage_id__in=cage_ids)

        pending_disease = disease_qs.filter(status='pending').count()
        pending_mortality = mortality_qs.filter(status='pending').count()
        pending_reports = pending_disease + pending_mortality
        total_reports = disease_qs.count() + mortality_qs.count()

        abnormal_cages = cages_qs.filter(status='abnormal').count()

        high_risk_areas = 0
        for area in sea_areas_qs:
            area_cages = area.cages.all()
            if cage_ids is not None:
                area_cages = area_cages.filter(id__in=cage_ids)
            abnormal = area_cages.filter(
                Q(disease_reports__status='pending') |
                Q(mortality_reports__status='pending') |
                Q(status='abnormal')
            ).distinct().count()
            if abnormal >= 3:
                high_risk_areas += 1

        farmers_with_issues = 0
        for f in farmers_qs:
            f_cages = Cage.objects.filter(cage_farmers__farmer=f)
            if cage_ids is not None:
                f_cages = f_cages.filter(id__in=cage_ids)
            f_cage_ids = list(f_cages.values_list('id', flat=True))
            has_pending = (
                DiseaseReport.objects.filter(cage_id__in=f_cage_ids, status='pending').exists()
                or MortalityReport.objects.filter(cage_id__in=f_cage_ids, status='pending').exists()
            )
            if has_pending:
                farmers_with_issues += 1

        def pct(part, whole):
            return round(part / whole * 100, 1) if whole else 0.0

        data = {
            'sea_areas_count': sea_areas,
            'cages_count': cages,
            'farmers_count': farmers,
            'pending_reports_count': pending_reports,
            'sea_areas_percentage': pct(high_risk_areas, sea_areas),
            'cages_percentage': pct(abnormal_cages, cages),
            'farmers_percentage': pct(farmers_with_issues, farmers),
            'pending_reports_percentage': pct(pending_reports, total_reports),
            'high_risk_areas': high_risk_areas,
            'abnormal_cages': abnormal_cages,
            'pending_disease': pending_disease,
            'pending_mortality': pending_mortality,
            'total_reports': total_reports,
            'farmers_with_issues': farmers_with_issues,
        }
        return Response(data)


class MonthlyTrendsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        from inspection.models import InspectionRecord
        trends = []
        now = timezone.now()
        user = request.user
        cage_ids = None
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)

        for i in range(5, -1, -1):
            month_start = (now - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                month_end = now
            else:
                next_month = (now - timedelta(days=(i - 1) * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = next_month - timedelta(days=1)

            disease_qs = DiseaseReport.objects.filter(
                report_time__gte=month_start,
                report_time__lte=month_end
            )
            mortality_qs = MortalityReport.objects.filter(
                report_time__gte=month_start,
                report_time__lte=month_end
            )
            if cage_ids is not None:
                disease_qs = disease_qs.filter(cage_id__in=cage_ids)
                mortality_qs = mortality_qs.filter(cage_id__in=cage_ids)

            disease_count = disease_qs.count()
            mortality_count = mortality_qs.count()
            total_mortality = sum(r.mortality_count for r in mortality_qs)
            inspection_count = InspectionRecord.objects.filter(
                created_at__gte=month_start,
                created_at__lte=month_end
            ).count()

            trends.append({
                'month': month_start.strftime('%Y-%m'),
                'disease_count': disease_count,
                'mortality_count': mortality_count,
                'inspection_count': inspection_count,
                'total_mortality': total_mortality,
            })

        return Response(trends)


class HeatmapDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        from accounts.permissions import is_farmer, get_farmer_cage_ids
        data = []
        seven_days_ago = timezone.now() - timedelta(days=7)
        user = request.user

        farmer_cage_ids = None
        if is_farmer(user):
            farmer_cage_ids = set(get_farmer_cage_ids(user))

        for area in SeaArea.objects.all():
            cages = area.cages.all()
            cage_ids = set(cages.values_list('id', flat=True))

            if farmer_cage_ids is not None:
                cage_ids = cage_ids & farmer_cage_ids
                if not cage_ids:
                    continue

            disease_reports = DiseaseReport.objects.filter(
                cage_id__in=cage_ids,
                report_time__gte=seven_days_ago
            ).count()

            mortality_reports = MortalityReport.objects.filter(
                cage_id__in=cage_ids,
                report_time__gte=seven_days_ago
            ).count()

            abnormal_cages = Cage.objects.filter(id__in=cage_ids).filter(
                Q(disease_reports__status='pending') |
                Q(mortality_reports__status='pending') |
                Q(status='abnormal')
            ).distinct().count()

            total_cages = len(cage_ids)
            risk_score = 0
            if total_cages > 0:
                risk_score = (abnormal_cages / total_cages) * 50 + (disease_reports + mortality_reports) * 2
                risk_score = min(risk_score, 100)

            risk_level = 'low'
            if risk_score >= 80:
                risk_level = 'critical'
            elif risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 20:
                risk_level = 'medium'

            data.append({
                'id': area.id,
                'name': area.name,
                'sea_area_id': area.id,
                'sea_area_name': area.name,
                'location': area.location,
                'lat': area.center_lat or 0,
                'lng': area.center_lng or 0,
                'total_cages': total_cages,
                'abnormal_cages': abnormal_cages,
                'disease_reports': disease_reports,
                'mortality_reports': mortality_reports,
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
            })

        return Response(data)


class FarmerResponsibilityView(APIView):
    permission_classes = [role_permission('admin', 'inspector', 'technician', 'farmer')]

    def get(self, request):
        from disease.models import DiseaseReport, MortalityReport
        from accounts.permissions import is_farmer, get_user_farmer
        data = []
        user = request.user

        farmers_qs = Farmer.objects.all()
        if is_farmer(user):
            current_farmer = get_user_farmer(user)
            if current_farmer:
                farmers_qs = Farmer.objects.filter(pk=current_farmer.pk)
            else:
                farmers_qs = Farmer.objects.none()

        for farmer in farmers_qs:
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

            responsibility_score = pending_disease + pending_mortality + anomaly_disease + anomaly_mortality
            risk_level = 'low'
            if responsibility_score >= 10:
                risk_level = 'critical'
            elif responsibility_score >= 5:
                risk_level = 'high'
            elif responsibility_score >= 2:
                risk_level = 'medium'

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
                'responsibility_score': responsibility_score,
                'risk_level': risk_level,
            })

        data.sort(key=lambda x: x['responsibility_score'], reverse=True)
        return Response(data)


class SeaAreaViewSet(viewsets.ModelViewSet):
    queryset = SeaArea.objects.all()
    serializer_class = SeaAreaSerializer
    permission_classes = [role_permission('admin')]
    filterset_fields = ['name', 'location']
    search_fields = ['name', 'location', 'description']
    ordering_fields = ['created_at', 'name', 'area']

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'high_risk_areas'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            queryset = queryset.filter(cages__id__in=cage_ids).distinct()
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
        from disease.models import DiseaseReport, MortalityReport
        threshold = float(request.query_params.get('threshold', 20))
        seven_days_ago = timezone.now() - timedelta(days=7)
        queryset = self.get_queryset()
        high_risk_areas = []
        for area in queryset:
            cages = area.cages.all()
            cage_ids = list(cages.values_list('id', flat=True))

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
            if risk_score >= 80:
                risk_level = 'critical'
            elif risk_score >= 50:
                risk_level = 'high'
            elif risk_score >= 20:
                risk_level = 'medium'

            if risk_score >= threshold:
                high_risk_areas.append({
                    'id': area.id,
                    'name': area.name,
                    'location': area.location,
                    'lat': area.center_lat or 0,
                    'lng': area.center_lng or 0,
                    'risk_score': round(risk_score, 2),
                    'risk_level': risk_level,
                    'abnormal_cage_count': abnormal_cages,
                    'total_cages': total_cages,
                    'disease_reports': disease_reports,
                    'mortality_reports': mortality_reports,
                })
        high_risk_areas.sort(key=lambda x: x['risk_score'], reverse=True)
        return Response(high_risk_areas)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        area = self.get_object()
        cages = area.cages.all()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            cages = cages.filter(id__in=cage_ids)
        total_capacity = sum(c.capacity for c in cages)
        status_stats = cages.values('status').annotate(count=Count('id'))
        farmers = area.farmers.all()
        if is_farmer(user):
            farmer = get_user_farmer(user)
            if farmer:
                farmers = Farmer.objects.filter(pk=farmer.pk)
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
    permission_classes = [role_permission('admin')]
    filterset_fields = ['name', 'phone', 'sea_area']
    search_fields = ['name', 'phone', 'id_card']
    ordering_fields = ['created_at', 'name', 'registration_date']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if is_farmer(user):
            farmer = get_user_farmer(user)
            if farmer:
                queryset = queryset.filter(pk=farmer.pk)
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
    permission_classes = [role_permission('admin')]
    filterset_fields = ['code', 'sea_area', 'status', 'species']
    search_fields = ['code', 'location', 'species']
    ordering_fields = ['created_at', 'code', 'capacity', 'stocking_date']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [role_permission('admin')()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        farmer_id = self.request.query_params.get('farmer')
        if farmer_id:
            queryset = queryset.filter(cage_farmers__farmer_id=farmer_id)
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            queryset = queryset.filter(id__in=cage_ids)
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
    permission_classes = [role_permission('admin')]
    filterset_fields = ['cage', 'farmer']
    search_fields = ['cage__code', 'farmer__name']
    ordering_fields = ['created_at', 'start_date', 'end_date']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if is_farmer(user):
            farmer = get_user_farmer(user)
            if farmer:
                queryset = queryset.filter(farmer=farmer)
        return queryset

