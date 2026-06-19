from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InspectionRouteViewSet, InspectionRecordViewSet, InspectionPointViewSet

router = DefaultRouter()
router.register(r'routes', InspectionRouteViewSet)
router.register(r'records', InspectionRecordViewSet)
router.register(r'points', InspectionPointViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
