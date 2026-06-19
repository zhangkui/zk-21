from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DiseaseReportViewSet, MortalityReportViewSet, AnomalyDetectionViewSet

router = DefaultRouter()
router.register(r'disease-reports', DiseaseReportViewSet)
router.register(r'mortality-reports', MortalityReportViewSet)
router.register(r'anomaly-detection', AnomalyDetectionViewSet, basename='anomaly-detection')

urlpatterns = [
    path('', include(router.urls)),
]
