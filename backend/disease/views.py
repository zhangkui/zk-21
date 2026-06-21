from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import timedelta
from .models import DiseaseReport, MortalityReport
from .serializers import DiseaseReportSerializer, MortalityReportSerializer
from .tasks import (
    detect_disease_anomalies,
    detect_mortality_anomalies,
    run_all_anomaly_detections,
    get_high_risk_areas_statistics
)
from accounts.permissions import (
    role_permission,
    is_admin,
    is_farmer,
    get_role_code,
    get_farmer_cage_ids,
)


def _is_admin(user):
    return is_admin(user)


def _resolve_reporter(request):
    user = request.user
    reporter = request.data.get('reporter', None) if isinstance(request.data, dict) else None
    if _is_admin(user):
        if reporter in (None, '', 'null'):
            return user
        try:
            from django.contrib.auth.models import User
            return User.objects.get(pk=int(reporter))
        except (ValueError, TypeError, User.DoesNotExist):
            return user
    return user


def _validate_cage_for_user(user, cage_id):
    if is_admin(user) or get_role_code(user) in ('inspector', 'technician'):
        return True
    if is_farmer(user):
        allowed_ids = get_farmer_cage_ids(user)
        return int(cage_id) in allowed_ids
    return False


class RecentReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = []
        limit = int(request.query_params.get('limit', 10))
        user = request.user

        disease_qs = DiseaseReport.objects.all()
        mortality_qs = MortalityReport.objects.all()
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            disease_qs = disease_qs.filter(cage_id__in=cage_ids)
            mortality_qs = mortality_qs.filter(cage_id__in=cage_ids)

        disease_reports = disease_qs.order_by('-report_time')[:limit]
        mortality_reports = mortality_qs.order_by('-report_time')[:limit]
        
        for r in disease_reports:
            reports.append({
                'id': r.id,
                'type': 'disease',
                'cage_code': r.cage.code if r.cage else '',
                'cage_id': r.cage.id if r.cage else None,
                'reporter': r.reporter.username if r.reporter else '',
                'description': r.description,
                'report_time': r.report_time.isoformat(),
                'title': f'病害上报 - {r.get_disease_type_display()}',
                'severity': r.severity,
                'status': r.status,
                'is_anomaly': r.is_anomaly,
                'anomaly_score': r.anomaly_score,
            })

        for r in mortality_reports:
            reports.append({
                'id': r.id,
                'type': 'mortality',
                'cage_code': r.cage.code if r.cage else '',
                'cage_id': r.cage.id if r.cage else None,
                'reporter': r.reporter.username if r.reporter else '',
                'description': r.description,
                'report_time': r.report_time.isoformat(),
                'title': f'死亡上报 - 死亡{r.mortality_count}尾',
                'mortality_count': r.mortality_count,
                'cause': r.cause,
                'status': r.status,
                'is_anomaly': r.is_anomaly,
                'anomaly_score': r.anomaly_score,
            })
        
        reports.sort(key=lambda x: x['report_time'], reverse=True)
        return Response(reports[:limit])


class DiseaseTrendsView(APIView):
    permission_classes = [role_permission('admin', 'technician')]

    def get(self, request):
        trends = []
        now = timezone.now()
        user = request.user
        cage_ids = None
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)

        for i in range(6):
            start_date = (now - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if i == 0:
                end_date = now
            else:
                next_month = (now - timedelta(days=(i - 1) * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_date = next_month - timedelta(days=1)

            base_qs = DiseaseReport.objects.filter(
                report_time__gte=start_date,
                report_time__lte=end_date,
            )
            if cage_ids:
                base_qs = base_qs.filter(cage_id__in=cage_ids)

            month_data = {
                'month': start_date.strftime('%Y-%m'),
                'bacterial': base_qs.filter(disease_type='bacterial').count(),
                'viral': base_qs.filter(disease_type='viral').count(),
                'parasitic': base_qs.filter(disease_type='parasitic').count(),
                'fungal': base_qs.filter(disease_type='fungal').count(),
                'nutritional': base_qs.filter(disease_type='nutritional').count(),
                'environmental': base_qs.filter(disease_type='environmental').count(),
                'other': base_qs.filter(disease_type='other').count(),
            }
            trends.append(month_data)
        
        trends.reverse()
        return Response(trends)


class MortalityStatsView(APIView):
    permission_classes = [role_permission('admin', 'technician')]

    def get(self, request):
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        user = request.user
        cage_ids = None
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)

        base_qs = MortalityReport.objects.all()
        if cage_ids:
            base_qs = base_qs.filter(cage_id__in=cage_ids)

        total_reports = base_qs.count()
        total_mortality = sum(r.mortality_count for r in base_qs)

        recent_qs = base_qs.filter(report_time__gte=thirty_days_ago)
        recent_mortality = sum(r.mortality_count for r in recent_qs)

        cause_stats = base_qs.values('cause').annotate(
            count=Count('id'),
            total_mortality=Sum('mortality_count')
        ).order_by('-total_mortality')

        cause_data = []
        for stat in cause_stats:
            cause_display = dict(MortalityReport.CAUSE_CHOICES).get(stat['cause'], stat['cause'])
            cause_data.append({
                'cause': stat['cause'],
                'cause_display': cause_display,
                'count': stat['count'],
                'total_mortality': stat['total_mortality'],
                'percentage': (stat['total_mortality'] / total_mortality * 100) if total_mortality > 0 else 0,
            })

        data = {
            'total_reports': total_reports,
            'total_mortality': total_mortality,
            'recent_30_days_reports': recent_qs.count(),
            'recent_30_days_mortality': recent_mortality,
            'cause_statistics': cause_data,
        }
        return Response(data)


class DiseaseReportViewSet(viewsets.ModelViewSet):
    queryset = DiseaseReport.objects.all()
    serializer_class = DiseaseReportSerializer
    permission_classes = [role_permission('admin', 'inspector', 'technician', 'farmer')]
    filterset_fields = ['cage', 'disease_type', 'severity', 'status', 'reporter', 'is_anomaly']
    search_fields = ['cage__code', 'description', 'treatment_method']
    ordering_fields = ['report_time', 'created_at', 'severity', 'anomaly_score']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        days = self.request.query_params.get('days', None)
        if days:
            try:
                days_int = int(days)
                cutoff = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(report_time__gte=cutoff)
            except ValueError:
                pass
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            queryset = queryset.filter(Q(cage_id__in=cage_ids))
        return queryset

    def perform_create(self, serializer):
        serializer.validated_data.pop('reporter', None)
        cage_id = self.request.data.get('cage')
        if cage_id and not _validate_cage_for_user(self.request.user, cage_id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('您无权选择此网箱')
        reporter = _resolve_reporter(self.request)
        serializer.save(reporter=reporter)

    def perform_update(self, serializer):
        user = self.request.user
        cage_id = self.request.data.get('cage')
        if cage_id and not _validate_cage_for_user(user, cage_id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('您无权选择此网箱')
        if not _is_admin(user):
            reporter = _resolve_reporter(self.request)
            serializer.validated_data.pop('reporter', None)
            serializer.save(reporter=reporter)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        report = self.get_object()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            if report.cage_id not in cage_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您无权处理此报告')
        if report.status == 'pending':
            report.status = 'processing'
            report.treated_by = request.data.get('treated_by', '')
            report.treatment_method = request.data.get('treatment_method', '')
            report.treatment_time = timezone.now()
            report.save()
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        return Response(
            {'error': f'无法处理状态为"{report.get_status_display()}"的报告'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        report = self.get_object()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            if report.cage_id not in cage_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您无权处理此报告')
        if report.status in ['pending', 'processing']:
            report.status = 'resolved'
            if not report.treatment_time:
                report.treatment_time = timezone.now()
            report.save()
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        return Response(
            {'error': f'无法解决状态为"{report.get_status_display()}"的报告'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        report = self.get_object()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            if report.cage_id not in cage_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您无权处理此报告')
        report.status = 'closed'
        report.save()
        serializer = self.get_serializer(report)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def anomaly_reports(self, request):
        queryset = self.get_queryset()
        anomaly_reports = queryset.filter(is_anomaly=True)
        serializer = self.get_serializer(anomaly_reports, many=True)
        return Response({
            'count': anomaly_reports.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        pending = queryset.filter(status='pending').count()
        processing = queryset.filter(status='processing').count()
        resolved = queryset.filter(status='resolved').count()
        closed = queryset.filter(status='closed').count()
        anomaly = queryset.filter(is_anomaly=True).count()
        
        type_stats = queryset.values('disease_type').annotate(count=Count('id'))
        severity_stats = queryset.values('severity').annotate(count=Count('id'))
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent = queryset.filter(report_time__gte=seven_days_ago).count()
        
        data = {
            'total': total,
            'pending': pending,
            'processing': processing,
            'resolved': resolved,
            'closed': closed,
            'anomaly': anomaly,
            'recent_7_days': recent,
            'type_statistics': list(type_stats),
            'severity_statistics': list(severity_stats),
        }
        return Response(data)

    @action(detail=False, methods=['post'])
    def run_detection(self, request):
        if not is_admin(request.user) and get_role_code(request.user) != 'technician':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('您无权执行此操作')
        task = detect_disease_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '病害异常检测任务已启动'
        })


class MortalityReportViewSet(viewsets.ModelViewSet):
    queryset = MortalityReport.objects.all()
    serializer_class = MortalityReportSerializer
    permission_classes = [role_permission('admin', 'inspector', 'technician', 'farmer')]
    filterset_fields = ['cage', 'cause', 'status', 'reporter', 'is_anomaly']
    search_fields = ['cage__code', 'description', 'treatment_method']
    ordering_fields = ['report_time', 'created_at', 'mortality_count', 'anomaly_score']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        days = self.request.query_params.get('days', None)
        if days:
            try:
                days_int = int(days)
                cutoff = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(report_time__gte=cutoff)
            except ValueError:
                pass
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            queryset = queryset.filter(Q(cage_id__in=cage_ids))
        return queryset

    def perform_create(self, serializer):
        serializer.validated_data.pop('reporter', None)
        cage_id = self.request.data.get('cage')
        if cage_id and not _validate_cage_for_user(self.request.user, cage_id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('您无权选择此网箱')
        reporter = _resolve_reporter(self.request)
        serializer.save(reporter=reporter)

    def perform_update(self, serializer):
        user = self.request.user
        cage_id = self.request.data.get('cage')
        if cage_id and not _validate_cage_for_user(user, cage_id):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('您无权选择此网箱')
        if _is_admin(user):
            reporter = _resolve_reporter(self.request)
            serializer.validated_data.pop('reporter', None)
            serializer.save(reporter=reporter)
        else:
            serializer.save()

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        report = self.get_object()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            if report.cage_id not in cage_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您无权处理此报告')
        if report.status == 'pending':
            report.status = 'processing'
            report.treated_by = request.data.get('treated_by', '')
            report.treatment_method = request.data.get('treatment_method', '')
            report.treatment_time = timezone.now()
            report.save()
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        return Response(
            {'error': f'无法处理状态为"{report.get_status_display()}"的报告'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        report = self.get_object()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            if report.cage_id not in cage_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您无权处理此报告')
        if report.status in ['pending', 'processing']:
            report.status = 'resolved'
            if not report.treatment_time:
                report.treatment_time = timezone.now()
            report.save()
            serializer = self.get_serializer(report)
            return Response(serializer.data)
        return Response(
            {'error': f'无法解决状态为"{report.get_status_display()}"的报告'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        report = self.get_object()
        user = request.user
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)
            if report.cage_id not in cage_ids:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('您无权处理此报告')
        report.status = 'closed'
        report.save()
        serializer = self.get_serializer(report)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def anomaly_reports(self, request):
        queryset = self.get_queryset()
        anomaly_reports = queryset.filter(is_anomaly=True)
        serializer = self.get_serializer(anomaly_reports, many=True)
        return Response({
            'count': anomaly_reports.count(),
            'results': serializer.data
        })

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        queryset = self.get_queryset()
        total = queryset.count()
        pending = queryset.filter(status='pending').count()
        processing = queryset.filter(status='processing').count()
        resolved = queryset.filter(status='resolved').count()
        closed = queryset.filter(status='closed').count()
        anomaly = queryset.filter(is_anomaly=True).count()
        
        total_mortality = sum(r.mortality_count for r in queryset)
        cause_stats = queryset.values('cause').annotate(
            count=Count('id'),
            total_mortality=Sum('mortality_count')
        )
        
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_reports = queryset.filter(report_time__gte=seven_days_ago)
        recent_mortality = sum(r.mortality_count for r in recent_reports)
        
        data = {
            'total_reports': total,
            'total_mortality': total_mortality,
            'pending': pending,
            'processing': processing,
            'resolved': resolved,
            'closed': closed,
            'anomaly': anomaly,
            'recent_7_days_reports': recent_reports.count(),
            'recent_7_days_mortality': recent_mortality,
            'cause_statistics': list(cause_stats),
        }
        return Response(data)

    @action(detail=False, methods=['post'])
    def run_detection(self, request):
        if not is_admin(request.user) and get_role_code(request.user) != 'technician':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('您无权执行此操作')
        task = detect_mortality_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '死亡异常检测任务已启动'
        })


class AnomalyDetectionViewSet(viewsets.ViewSet):
    permission_classes = [role_permission('admin', 'technician')]
    
    @action(detail=False, methods=['post'])
    def run_all(self, request):
        task = run_all_anomaly_detections.delay()
        return Response({
            'task_id': task.id,
            'status': 'pending',
            'message': '所有异常检测任务已启动'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def run_disease(self, request):
        task = detect_disease_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'pending',
            'message': '病害异常检测任务已启动'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def run_mortality(self, request):
        task = detect_mortality_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'pending',
            'message': '死亡异常检测任务已启动'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'])
    def task_status(self, request):
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response(
                {'error': '缺少 task_id 参数'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        
        response_data = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
        }
        
        if result.ready():
            if result.successful():
                response_data['result'] = result.result
            else:
                response_data['error'] = str(result.result)
        
        return Response(response_data)

    @action(detail=False, methods=['get'])
    def high_risk_areas(self, request):
        from core.models import SeaArea, Cage
        data = []
        seven_days_ago = timezone.now() - timedelta(days=7)
        user = request.user
        user_cage_ids = None
        if is_farmer(user):
            user_cage_ids = get_farmer_cage_ids(user)
        
        for area in SeaArea.objects.all():
            cages = area.cages.all()
            cage_ids = list(cages.values_list('id', flat=True))
            if user_cage_ids is not None:
                cage_ids = [cid for cid in cage_ids if cid in user_cage_ids]

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
            
            anomaly_disease = DiseaseReport.objects.filter(
                cage_id__in=cage_ids,
                report_time__gte=seven_days_ago,
                is_anomaly=True
            ).count()
            
            anomaly_mortality = MortalityReport.objects.filter(
                cage_id__in=cage_ids,
                report_time__gte=seven_days_ago,
                is_anomaly=True
            ).count()
            
            total_cages = len(cage_ids)
            risk_score = 0
            if total_cages > 0:
                risk_score = (abnormal_cages / total_cages) * 40 + (disease_reports + mortality_reports) * 2 + (anomaly_disease + anomaly_mortality) * 5
                risk_score = min(risk_score, 100)
            
            risk_level = 'low'
            if risk_score >= 60:
                risk_level = 'high'
            elif risk_score >= 30:
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
                'anomaly_disease': anomaly_disease,
                'anomaly_mortality': anomaly_mortality,
                'risk_score': round(risk_score, 2),
                'risk_level': risk_level,
            })
        
        data.sort(key=lambda x: x['risk_score'], reverse=True)
        return Response(data)

    @action(detail=False, methods=['get'])
    def high_risk_summary(self, request):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        user = request.user
        cage_ids = None
        if is_farmer(user):
            cage_ids = get_farmer_cage_ids(user)

        disease_qs = DiseaseReport.objects.filter(
            is_anomaly=True,
            report_time__gte=start_date
        )
        mortality_qs = MortalityReport.objects.filter(
            is_anomaly=True,
            report_time__gte=start_date
        )
        pending_disease_qs = DiseaseReport.objects.filter(status='pending')
        pending_mortality_qs = MortalityReport.objects.filter(status='pending')
        high_severity_qs = DiseaseReport.objects.filter(
            severity__in=['severe', 'critical'],
            status='pending'
        )
        high_mortality_qs = MortalityReport.objects.filter(
            report_time__gte=start_date
        )

        if cage_ids:
            disease_qs = disease_qs.filter(cage_id__in=cage_ids)
            mortality_qs = mortality_qs.filter(cage_id__in=cage_ids)
            pending_disease_qs = pending_disease_qs.filter(cage_id__in=cage_ids)
            pending_mortality_qs = pending_mortality_qs.filter(cage_id__in=cage_ids)
            high_severity_qs = high_severity_qs.filter(cage_id__in=cage_ids)
            high_mortality_qs = high_mortality_qs.filter(cage_id__in=cage_ids)

        disease_anomalies = disease_qs.count()
        mortality_anomalies = mortality_qs.count()
        pending_disease = pending_disease_qs.count()
        pending_mortality = pending_mortality_qs.count()
        high_severity = high_severity_qs.count()
        high_mortality_cages = high_mortality_qs.values('cage').annotate(
            total=Sum('mortality_count')
        ).filter(total__gte=50).count()
        
        data = {
            'period_days': 7,
            'disease_anomalies': disease_anomalies,
            'mortality_anomalies': mortality_anomalies,
            'total_anomalies': disease_anomalies + mortality_anomalies,
            'pending_disease_reports': pending_disease,
            'pending_mortality_reports': pending_mortality,
            'pending_total': pending_disease + pending_mortality,
            'high_severity_disease': high_severity,
            'high_mortality_cages': high_mortality_cages,
            'calculated_at': timezone.now().isoformat()
        }
        return Response(data)
