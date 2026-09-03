from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import (
    AnimalViewSet, 
    CageViewSet, 
    RackPositionViewSet,
    HusbandryEventViewSet,
    AuditOperationViewSet,
    )

from colony.views import CurrentUserView

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

router.register(
    r"audit-operations",
    AuditOperationViewSet,
    basename="audit-operation",
)

# urlpatterns = router.urls
urlpatterns = [
    path(
        "auth/me/",
        CurrentUserView.as_view(),
        name="current-user",
    ),

    path(
        "",
        include(router.urls),
    ),
]