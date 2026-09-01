from rest_framework.routers import DefaultRouter

from .views import AnimalViewSet, CageViewSet


router = DefaultRouter()

router.register(
    "animals",
    AnimalViewSet,
    basename="animal",
)

router.register(
    "cages",
    CageViewSet,
    basename="cage",
)

urlpatterns = router.urls