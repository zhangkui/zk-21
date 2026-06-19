from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q
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


class RecentReportsView(APIView):
    def get(self, request):
        try:
            reports = []
            limit = int(request.query_params.get('limit', 10))
            
            disease_reports = DiseaseReport.objects.all().order_by('-report_time')[:limit]
            mortality_reports = MortalityReport.objects.all().order_by('-report_time')[:limit]
            
            for r in disease_reports:
                reports.append({
                    'id': r.id,
                    'type': 'disease',
                    'cage_code': r.cage.code if r.cage else '',
                    'cage_id': r.cage.id if r.cage else None,
                    'reporter': r.reporter,
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
                    'reporter': r.reporter,
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
        except Exception as e:
            return Response([])


class DiseaseTrendsView(APIView):
    def get(self, request):
        try:
            trends = []
            now = timezone.now()
            
            for i in range(6):
                start_date = (now - timedelta(days=i * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if i == 0:
                    end_date = now
                else:
                    next_month = (now - timedelta(days=(i - 1) * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    end_date = next_month - timedelta(days=1)
                
                month_data = {
                    'month': start_date.strftime('%Y-%m'),
                    'bacterial': DiseaseReport.objects.filter(
                        report_time__gte=start_date,
                        report_time__lte=end_date,
                        disease_type='bacterial'
                    ).count(),
                    'viral': DiseaseReport.objects.filter(
                        report_time__gte=start_date,
                        report_time__lte=end_date,
                        disease_type='viral'
                    ).count(),
                    'parasitic': DiseaseReport.objects.filter(
                        report_time__gte=start_date,
                        report_time__lte=end_date,
                        disease_type='parasitic'
                    ).count(),
                    'fungal': DiseaseReport.objects.filter(
                        report_time__gte=start_date,
                        report_time__lte=end_date,
                        disease_type='fungal'
                    ).count(),
                    'other': DiseaseReport.objects.filter(
                        report_time__gte=start_date,
                        report_time__lte=end_date,
                        disease_type__in=['nutritional', 'environmental', 'other']
                    ).count(),
                }
                trends.append(month_data)
            
            trends.reverse()
            return Response(trends)
        except Exception as e:
            return Response([])


class MortalityStatsView(APIView):
    def get(self, request):
        try:
            now = timezone.now()
            thirty_days_ago = now - timedelta(days=30)
            
            total_reports = MortalityReport.objects.count()
            total_mortality = sum(r.mortality_count for r in MortalityReport.objects.all())
            
            recent_reports = MortalityReport.objects.filter(report_time__gte=thirty_days_ago)
            recent_mortality = sum(r.mortality_count for r in recent_reports)
            
            cause_stats = MortalityReport.objects.values('cause').annotate(
                count=Count('id'),
                total_mortality=Count('mortality_count')
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
                'recent_30_days_reports': recent_reports.count(),
                'recent_30_days_mortality': recent_mortality,
                'cause_statistics': cause_data,
            }
            return Response(data)
        except Exception as e:
            return Response({
                'total_reports': 0,
                'total_mortality': 0,
                'recent_30_days_reports': 0,
                'recent_30_days_mortality': 0,
                'cause_statistics': [],
            })


class DiseaseReportViewSet(viewsets.ModelViewSet):
    queryset = DiseaseReport.objects.all()
    serializer_class = DiseaseReportSerializer
    filterset_fields = ['cage', 'disease_type', 'severity', 'status', 'reporter', 'is_anomaly']
    search_fields = ['cage__code', 'reporter', 'description', 'treatment_method']
    ordering_fields = ['report_time', 'created_at', 'severity', 'anomaly_score']

    def get_queryset(self):
        queryset = super().get_queryset()
        days = self.request.query_params.get('days', None)
        if days:
            try:
                days_int = int(days)
                cutoff = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(report_time__gte=cutoff)
            except ValueError:
                pass
        return queryset

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        report = self.get_object()
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
        task = detect_disease_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '病害异常检测任务已启动'
        })


class MortalityReportViewSet(viewsets.ModelViewSet):
    queryset = MortalityReport.objects.all()
    serializer_class = MortalityReportSerializer
    filterset_fields = ['cage', 'cause', 'status', 'reporter', 'is_anomaly']
    search_fields = ['cage__code', 'reporter', 'description', 'treatment_method']
    ordering_fields = ['report_time', 'created_at', 'mortality_count', 'anomaly_score']

    def get_queryset(self):
        queryset = super().get_queryset()
        days = self.request.query_params.get('days', None)
        if days:
            try:
                days_int = int(days)
                cutoff = timezone.now() - timedelta(days=days_int)
                queryset = queryset.filter(report_time__gte=cutoff)
            except ValueError:
                pass
        return queryset

    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        report = self.get_object()
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
            total_mortality=Count('mortality_count')
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
        task = detect_mortality_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '死亡异常检测任务已启动'
        })


class AnomalyDetectionViewSet(viewsets.ViewSet):
    
    @action(detail=False, methods=['post'])
    def run_all(self, request):
        task = run_all_anomaly_detections.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '所有异常检测任务已启动'
        })

    @action(detail=False, methods=['post'])
    def run_disease(self, request):
        task = detect_disease_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '病害异常检测任务已启动'
        })

    @action(detail=False, methods=['post'])
    def run_mortality(self, request):
        task = detect_mortality_anomalies.delay()
        return Response({
            'task_id': task.id,
            'status': 'started',
            'message': '死亡异常检测任务已启动'
        })

    @action(detail=False, methods=['get'])
    def high_risk_areas(self, request):
        task_result = get_high_risk_areas_statistics.delay()
        task_result.wait()
        return Response(task_result.result)

    @action(detail=False, methods=['get'])
    def high_risk_summary(self, request):
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        disease_anomalies = DiseaseReport.objects.filter(
            is_anomaly=True,
            report_time__gte=start_date
        ).count()
        
        mortality_anomalies = MortalityReport.objects.filter(
            is_anomaly=True,
            report_time__gte=start_date
        ).count()
        
        pending_disease = DiseaseReport.objects.filter(status='pending').count()
        pending_mortality = MortalityReport.objects.filter(status='pending').count()
        
        high_severity = DiseaseReport.objects.filter(
            severity__in=['severe', 'critical'],
            status='pending'
        ).count()
        
        high_mortality_cages = MortalityReport.objects.filter(
            report_time__gte=start_date
        ).values('cage').annotate(
            total=Count('mortality_count')
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
