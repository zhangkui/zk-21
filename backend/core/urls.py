from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SeaAreaViewSet, FarmerViewSet, CageViewSet, CageFarmerViewSet,
    DashboardStatsView, MonthlyTrendsView, HeatmapDataView, FarmerResponsibilityView
)

router = DefaultRouter()
router.register(r'sea-areas', SeaAreaViewSet)
router.register(r'farmers', FarmerViewSet)
router.register(r'cages', CageViewSet)
router.register(r'cage-farmers', CageFarmerViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('dashboard/monthly_trends/', MonthlyTrendsView.as_view(), name='monthly-trends'),
    path('analytics/heatmap/', HeatmapDataView.as_view(), name='heatmap-data'),
    path('analytics/farmer_responsibility/', FarmerResponsibilityView.as_view(), name='farmer-responsibility'),
]
