from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DiseaseReportViewSet, MortalityReportViewSet, AnomalyDetectionViewSet,
    RecentReportsView, DiseaseTrendsView, MortalityStatsView
)

router = DefaultRouter()
router.register(r'disease-reports', DiseaseReportViewSet)
router.register(r'mortality-reports', MortalityReportViewSet)
router.register(r'anomaly-detection', AnomalyDetectionViewSet, basename='anomaly-detection')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/recent_reports/', RecentReportsView.as_view(), name='recent-reports'),
    path('analytics/disease_trends/', DiseaseTrendsView.as_view(), name='disease-trends'),
    path('analytics/mortality_stats/', MortalityStatsView.as_view(), name='mortality-stats'),
]
