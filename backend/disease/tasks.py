from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from .models import DiseaseReport, MortalityReport
from core.models import Cage, SeaArea
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def detect_disease_anomalies(self):
    logger.info('开始病害异常检测任务...')
    
    threshold_recent_days = 7
    high_report_count_threshold = 3
    high_severity_count_threshold = 2
    rapid_increase_ratio = 2.0
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=threshold_recent_days)
    prev_start_date = start_date - timedelta(days=threshold_recent_days)
    
    updated_count = 0
    
    cages = Cage.objects.all()
    for cage in cages:
        recent_reports = DiseaseReport.objects.filter(
            cage=cage,
            report_time__gte=start_date,
            report_time__lte=end_date
        )
        prev_reports = DiseaseReport.objects.filter(
            cage=cage,
            report_time__gte=prev_start_date,
            report_time__lt=start_date
        )
        
        recent_count = recent_reports.count()
        prev_count = prev_reports.count()
        
        high_severity_count = recent_reports.filter(
            severity__in=['severe', 'critical']
        ).count()
        
        is_anomaly = False
        anomaly_score = 0.0
        
        if recent_count >= high_report_count_threshold:
            is_anomaly = True
            anomaly_score += min(recent_count * 0.2, 0.4)
        
        if high_severity_count >= high_severity_count_threshold:
            is_anomaly = True
            anomaly_score += min(high_severity_count * 0.15, 0.3)
        
        if prev_count > 0 and recent_count / prev_count >= rapid_increase_ratio:
            is_anomaly = True
            anomaly_score += 0.2
        
        if cage.status == 'abnormal':
            anomaly_score += 0.1
        
        anomaly_score = min(anomaly_score, 1.0)
        
        reports_to_update = recent_reports.filter(is_anomaly=False)
        for report in reports_to_update:
            report.is_anomaly = is_anomaly
            report.anomaly_score = anomaly_score
            report.save(update_fields=['is_anomaly', 'anomaly_score', 'updated_at'])
            updated_count += 1
    
    logger.info(f'病害异常检测完成，更新了 {updated_count} 条记录')
    return {
        'task': 'detect_disease_anomalies',
        'updated_count': updated_count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(bind=True)
def detect_mortality_anomalies(self):
    logger.info('开始死亡异常检测任务...')
    
    threshold_recent_days = 7
    high_mortality_count_threshold = 100
    high_mortality_rate_threshold = 0.05
    rapid_increase_ratio = 2.0
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=threshold_recent_days)
    prev_start_date = start_date - timedelta(days=threshold_recent_days)
    
    updated_count = 0
    
    cages = Cage.objects.all()
    for cage in cages:
        recent_reports = MortalityReport.objects.filter(
            cage=cage,
            report_time__gte=start_date,
            report_time__lte=end_date
        )
        prev_reports = MortalityReport.objects.filter(
            cage=cage,
            report_time__gte=prev_start_date,
            report_time__lt=start_date
        )
        
        total_mortality = sum(r.mortality_count for r in recent_reports)
        prev_total_mortality = sum(r.mortality_count for r in prev_reports)
        
        is_anomaly = False
        anomaly_score = 0.0
        
        if total_mortality >= high_mortality_count_threshold:
            is_anomaly = True
            anomaly_score += min(total_mortality / 500, 0.4)
        
        if cage.capacity > 0:
            mortality_rate = total_mortality / cage.capacity
            if mortality_rate >= high_mortality_rate_threshold:
                is_anomaly = True
                anomaly_score += min(mortality_rate * 2, 0.3)
        
        if prev_total_mortality > 0 and total_mortality / prev_total_mortality >= rapid_increase_ratio:
            is_anomaly = True
            anomaly_score += 0.2
        
        unknown_cause_count = recent_reports.filter(cause='unknown').count()
        if unknown_cause_count >= 2:
            anomaly_score += 0.1
        
        anomaly_score = min(anomaly_score, 1.0)
        
        reports_to_update = recent_reports.filter(is_anomaly=False)
        for report in reports_to_update:
            report.is_anomaly = is_anomaly
            report.anomaly_score = anomaly_score
            report.save(update_fields=['is_anomaly', 'anomaly_score', 'updated_at'])
            updated_count += 1
    
    logger.info(f'死亡异常检测完成，更新了 {updated_count} 条记录')
    return {
        'task': 'detect_mortality_anomalies',
        'updated_count': updated_count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(bind=True)
def run_all_anomaly_detections(self):
    logger.info('开始执行所有异常检测任务...')
    
    disease_result = detect_disease_anomalies.delay()
    mortality_result = detect_mortality_anomalies.delay()
    
    disease_result.wait()
    mortality_result.wait()
    
    logger.info('所有异常检测任务完成')
    return {
        'disease_detection': disease_result.result,
        'mortality_detection': mortality_result.result,
        'timestamp': timezone.now().isoformat()
    }


@shared_task(bind=True)
def get_high_risk_areas_statistics(self):
    logger.info('开始计算高风险区域统计...')
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    areas = SeaArea.objects.all()
    statistics = []
    
    for area in areas:
        cages = area.cages.all()
        cage_ids = cages.values_list('id', flat=True)
        
        disease_reports = DiseaseReport.objects.filter(
            cage_id__in=cage_ids,
            report_time__gte=start_date,
            status='pending'
        )
        mortality_reports = MortalityReport.objects.filter(
            cage_id__in=cage_ids,
            report_time__gte=start_date,
            status='pending'
        )
        
        abnormal_cages = cages.filter(
            Q(status='abnormal') |
            Q(disease_reports__in=disease_reports) |
            Q(mortality_reports__in=mortality_reports)
        ).distinct()
        
        anomaly_reports = disease_reports.filter(is_anomaly=True).count() + \
                          mortality_reports.filter(is_anomaly=True).count()
        
        risk_level = 'low'
        if abnormal_cages.count() >= 5 or anomaly_reports >= 3:
            risk_level = 'high'
        elif abnormal_cages.count() >= 2 or anomaly_reports >= 1:
            risk_level = 'medium'
        
        statistics.append({
            'sea_area_id': area.id,
            'sea_area_name': area.name,
            'location': area.location,
            'total_cages': cages.count(),
            'abnormal_cages': abnormal_cages.count(),
            'pending_disease_reports': disease_reports.count(),
            'pending_mortality_reports': mortality_reports.count(),
            'anomaly_reports': anomaly_reports,
            'risk_level': risk_level,
            'calculated_at': timezone.now().isoformat()
        })
    
    statistics.sort(key=lambda x: x['anomaly_reports'], reverse=True)
    
    logger.info(f'高风险区域统计完成，共 {len(statistics)} 个海区')
    return {
        'statistics': statistics,
        'high_risk_count': sum(1 for s in statistics if s['risk_level'] == 'high'),
        'medium_risk_count': sum(1 for s in statistics if s['risk_level'] == 'medium'),
        'low_risk_count': sum(1 for s in statistics if s['risk_level'] == 'low'),
        'timestamp': timezone.now().isoformat()
    }
