from rest_framework.routers import DefaultRouter
from django.urls import include, path

from .views import (
    AnimalViewSet, 
    CageViewSet, 
    RackPositionViewSet,
    HusbandryEventViewSet,
    AuditOperationViewSet,
    AnimalImportPreviewView,
    AnimalImportCommitView,
    AnimalImportUndoView,
    ColonyUserListView,
    )

from colony.views import CurrentUserView
from colony.export_views import (
    AnimalCensusCsvExportView,
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
    path(
        "imports/animals/preview/",
        AnimalImportPreviewView.as_view(),
        name="animal-import-preview",
    ),
    path(
        "imports/animals/<int:batch_id>/commit/",
        AnimalImportCommitView.as_view(),
        name="animal-import-commit",
    ),
    path(
        "imports/animals/<int:batch_id>/undo/",
        AnimalImportUndoView.as_view(),
        name="animal-import-undo",
    ),
    path(
        "exports/animal-census.csv",
        AnimalCensusCsvExportView.as_view(),
        name="animal-census-export",
    ),
    path(
        "users/",
        ColonyUserListView.as_view(),
        name="colony-user-list",
    ),
]