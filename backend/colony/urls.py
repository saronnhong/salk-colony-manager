from rest_framework.routers import DefaultRouter

from .views import (
    AnimalViewSet, 
    CageViewSet, 
    RackPositionViewSet,
    HusbandryEventViewSet
    )


router = DefaultRouter()

router.register(
    "animals",
    AnimalViewSet,
    basename="animal",
)

router.register(
    r"cages",
    CageViewSet,
    basename="cage",
)

router.register(
    r"rack-positions",
    RackPositionViewSet,
    basename="rack-position",
)

router.register(
    r"husbandry-events",
    HusbandryEventViewSet,
    basename="husbandry-event",
)

urlpatterns = router.urls