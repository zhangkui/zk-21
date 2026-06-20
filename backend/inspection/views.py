from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import InspectionRoute, InspectionRecord, InspectionPoint
from .serializers import (
    InspectionRouteSerializer,
    InspectionRecordSerializer,
    InspectionRecordDetailSerializer,
    InspectionPointSerializer
)
from core.serializers import CageSerializer


class InspectionRouteViewSet(viewsets.ModelViewSet):
    queryset = InspectionRoute.objects.all()
    serializer_class = InspectionRouteSerializer
    filterset_fields = ['name']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            cage_count=Count('cages', distinct=True),
            record_count=Count('records', distinct=True)
        )
        return queryset

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['get'])
    def cages(self, request, pk=None):
        route = self.get_object()
        cages = route.cages.all()
        serializer = CageSerializer(cages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def records(self, request, pk=None):
        route = self.get_object()
        records = route.records.all()
        serializer = InspectionRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        data = {
            'total_routes': total,
            'total_cages': sum(route.cages.count() for route in queryset),
            'total_records': sum(route.records.count() for route in queryset),
        }
        return Response(data)


class InspectionRecordViewSet(viewsets.ModelViewSet):
    queryset = InspectionRecord.objects.all()
    filterset_fields = ['route', 'inspector', 'status']
    search_fields = ['route__name', 'remarks']
    ordering_fields = ['created_at', 'start_time', 'end_time']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InspectionRecordDetailSerializer
        return InspectionRecordSerializer

    def perform_create(self, serializer):
        inspector = serializer.validated_data.get('inspector')
        user = self.request.user
        if inspector is None and user and user.is_authenticated:
            inspector = user
            serializer.validated_data['inspector'] = inspector
        serializer.save(inspector=inspector)

    def perform_update(self, serializer):
        user = self.request.user
        inspector = serializer.validated_data.get('inspector', None)
        if 'inspector' not in serializer.validated_data:
            instance = serializer.instance
            inspector = instance.inspector
        if inspector is None and user and user.is_authenticated:
            inspector = user
        serializer.save(inspector=inspector)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(
            point_count=Count('points', distinct=True),
            abnormal_count=Count(
                'points',
                filter=Q(points__has_abnormality=True),
                distinct=True
            )
        )
        return queryset

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        record = self.get_object()
        if record.status == 'pending':
            record.status = 'in_progress'
            record.start_time = timezone.now()
            record.save()
            serializer = self.get_serializer(record)
            return Response(serializer.data)
        return Response(
            {'error': f'无法开始状态为"{record.get_status_display()}"的巡检'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        record = self.get_object()
        if record.status == 'in_progress':
            record.status = 'completed'
            record.end_time = timezone.now()
            record.save()
            serializer = self.get_serializer(record)
            return Response(serializer.data)
        return Response(
            {'error': f'无法完成状态为"{record.get_status_display()}"的巡检'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        record = self.get_object()
        if record.status in ['pending', 'in_progress']:
            record.status = 'cancelled'
            record.save()
            serializer = self.get_serializer(record)
            return Response(serializer.data)
        return Response(
            {'error': f'无法取消状态为"{record.get_status_display()}"的巡检'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        status_stats = queryset.values('status').annotate(count=Count('id'))
        
        today = timezone.now().date()
        today_records = queryset.filter(created_at__date=today).count()
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_records = queryset.filter(created_at__gte=seven_days_ago).count()
        
        abnormal_records = queryset.filter(abnormal_count__gt=0).count()
        
        data = {
            'total_records': total,
            'today_records': today_records,
            'recent_records': recent_records,
            'abnormal_records': abnormal_records,
            'status_statistics': list(status_stats),
        }
        return Response(data)


class InspectionPointViewSet(viewsets.ModelViewSet):
    queryset = InspectionPoint.objects.all()
    serializer_class = InspectionPointSerializer
    filterset_fields = ['record', 'cage', 'water_quality', 'has_abnormality']
    search_fields = ['cage__code', 'abnormal_condition']
    ordering_fields = ['check_time', 'created_at', 'water_temperature', 'ph_value']

    @action(detail=False, methods=['get'])
    def abnormal_points(self, request):
        queryset = self.get_queryset()
        abnormal_points = queryset.filter(has_abnormality=True)
        serializer = self.get_serializer(abnormal_points, many=True)
        return Response({
            'count': abnormal_points.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        abnormal_count = queryset.filter(has_abnormality=True).count()
        water_quality_stats = queryset.values('water_quality').annotate(count=Count('id'))
        
        avg_temp = queryset.filter(water_temperature__isnull=False).aggregate(
            avg=Count('water_temperature')
        )
        avg_ph = queryset.filter(ph_value__isnull=False).aggregate(
            avg=Count('ph_value')
        )
        
        data = {
            'total_points': total,
            'abnormal_count': abnormal_count,
            'abnormal_rate': (abnormal_count / total * 100) if total > 0 else 0,
            'water_quality_statistics': list(water_quality_stats),
        }
        return Response(data)
