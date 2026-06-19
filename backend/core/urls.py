from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SeaAreaViewSet, FarmerViewSet, CageViewSet, CageFarmerViewSet

router = DefaultRouter()
router.register(r'sea-areas', SeaAreaViewSet)
router.register(r'farmers', FarmerViewSet)
router.register(r'cages', CageViewSet)
router.register(r'cage-farmers', CageFarmerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
