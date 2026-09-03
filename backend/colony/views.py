from django.shortcuts import render
from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny, IsAuthenticated

# from .models import Animal, Cage, RackPosition
from .serializers import (
    AnimalMoveSerializer,
    AnimalSerializer,
    CageSerializer,
    CageSummarySerializer,
    RackPositionSummarySerializer,
)

from .services.animal_moves import move_animal

from colony.models import (
    Animal, 
    Cage, 
    RackPosition,
    Cage, 
    RackPosition, 
    CageRackPositionAssignment, 
    AnimalCageAssignment, 
    HusbandryEvent
    )
from colony.serializers import (
    CageMoveSerializer,
    CageSerializer,
    CageSummarySerializer,
    CageLocationHistorySerializer,
    AnimalLocationHistorySerializer,
    HusbandryEventSerializer,
    HusbandryEventCorrectionSerializer,
)
from colony.services.cage_moves import move_cage
from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny

from colony.services.husbandry_corrections import (
    correct_husbandry_event,
)

from colony.models import AuditOperation
from colony.serializers import AuditOperationSerializer
from colony.services.undo_operations import (
    undo_animal_move,
    undo_cage_move,
)
from rest_framework.views import APIView
from colony.serializers import CurrentUserSerializer


class AnimalViewSet(ReadOnlyModelViewSet):
    serializer_class = AnimalSerializer

    queryset = (
        Animal.objects
        .select_related("strain")
        .prefetch_related("local_identifiers")
        .order_by("-created_at")
    )

    @action(
        detail=True,
        methods=["post"],
        url_path="move",
        # permission_classes=[IsAuthenticated],
        permission_classes=[AllowAny],
    )
    def move(self, request, pk=None):
        animal = self.get_object()

        serializer = AnimalMoveSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        destination_cage = Cage.objects.get(
            id=serializer.validated_data[
                "destination_cage_id"
            ]
        )

        performed_by=request.user

        if not performed_by.is_authenticated:
            performed_by = (
                get_user_model()
                .objects
                .filter(is_superuser=True)
                .first()
            )


        try:
            move_animal(
                animal=animal,
                destination_cage=destination_cage,
                performed_by=performed_by,
                moved_at=serializer.validated_data.get(
                    "moved_at"
                ),
                reason=serializer.validated_data.get(
                    "reason",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        animal.refresh_from_db()

        return Response(
            AnimalSerializer(animal).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="location-history",
    )
    def location_history(self, request, pk=None):
        animal = self.get_object()

        assignments = (
            AnimalCageAssignment.objects
            .filter(animal=animal)
            .select_related("cage")
            .order_by("-valid_from")
        )

        serializer = AnimalLocationHistorySerializer(
            assignments,
            many=True,
        )

        return Response(serializer.data)
    


class CageViewSet(ReadOnlyModelViewSet):
    queryset = (
        Cage.objects
        .select_related(
            "current_location__rack_position__rack__current_room__room",
        )
        .prefetch_related(
            "animal_assignments__animal",
            "animal_assignments__animal__local_identifiers",
            "responsibilities__user",
        )
        .order_by("cage_code")
    )

    def get_serializer_class(self):
        if self.action == "list":
            return CageSummarySerializer

        return CageSerializer

    @action(
        detail=True,
        methods=["get"],
        url_path="animals",
    )
    def animals(self, request, pk=None):
        cage = self.get_object()

        assignments = (
            cage.animal_assignments
            .filter(
                valid_to__isnull=True,
                system_to__isnull=True,
            )
            .select_related("animal")
            .prefetch_related(
                "animal__local_identifiers",
            )
        )

        animals = [
            assignment.animal
            for assignment in assignments
        ]

        from .serializers import AnimalSummarySerializer

        serializer = AnimalSummarySerializer(
            animals,
            many=True,
        )

        return Response(serializer.data)
    
    @action(
        detail=True,
        methods=["post"],
        url_path="move",
        # permission_classes=[IsAuthenticated],
        permission_classes=[AllowAny],
    )
    def move(self, request, pk=None):
        cage = self.get_object()

        serializer = CageMoveSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        destination_position = RackPosition.objects.get(
            id=serializer.validated_data[
                "destination_rack_position_id"
            ]
        )

        performed_by=request.user

        if not performed_by.is_authenticated:
            performed_by = (
                get_user_model()
                .objects
                .filter(is_superuser=True)
                .first()
            )

        try:
            move_cage(
                cage=cage,
                destination_position=destination_position,
                performed_by=performed_by,
                moved_at=serializer.validated_data.get(
                    "moved_at"
                ),
                reason=serializer.validated_data.get(
                    "reason",
                    "",
                ),
            )
        except DjangoValidationError as exc:
            return Response(
                {
                    "detail": exc.messages,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        cage.refresh_from_db()

        return Response(
            CageSerializer(cage).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="location-history",
    )
    def location_history(self, request, pk=None):
        cage = self.get_object()

        assignments = (
            CageRackPositionAssignment.objects
                .filter(cage=cage)
                .select_related(
                    "rack_position",
                    "rack_position__rack",
                )
                .order_by("-valid_from")
        )

        serializer = CageLocationHistorySerializer(
            assignments,
            many=True,
        )

        return Response(serializer.data)

class RackPositionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RackPositionSummarySerializer
    permission_classes = [AllowAny]

    queryset = (
        RackPosition.objects
        .filter(retired_at__isnull=True)
        .select_related(
            "rack",
            "rack__current_room__room",
        )
        .order_by(
            "rack__rack_code",
            "position_label",
        )
    )

class HusbandryEventViewSet(viewsets.ModelViewSet):
    serializer_class = HusbandryEventSerializer
    permission_classes = [AllowAny]  # temporary during frontend development

    queryset = (
        HusbandryEvent.objects
        .select_related(
            "animal",
            "cage",
            "litter",
            "recorded_by",
        )
        .order_by("-event_datetime", "-recorded_at")
    )

    @action(
        detail=True,
        methods=["post"],
        url_path="correct",
    )
    def correct(self, request, pk=None):
        original_event = self.get_object()

        serializer = HusbandryEventCorrectionSerializer(
            data=request.data
        )

        serializer.is_valid(raise_exception=True)

        performed_by = request.user

        if not performed_by.is_authenticated:
            performed_by = (
                get_user_model()
                .objects
                .filter(is_superuser=True)
                .first()
            )

        try:
            corrected_event = correct_husbandry_event(
                original_event=original_event,
                recorded_by=performed_by,
                **serializer.validated_data,
            )
        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = HusbandryEventSerializer(
            corrected_event
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def get_queryset(self):
        queryset = super().get_queryset()

        animal_id = self.request.query_params.get("animal")

        if animal_id:
            queryset = queryset.filter(
                animal_id=animal_id
            )

        return queryset

    def perform_create(self, serializer):
        performed_by = self.request.user

        if not performed_by.is_authenticated:
            performed_by = (
                get_user_model()
                .objects
                .filter(is_superuser=True)
                .first()
            )

        serializer.save(
            recorded_by=performed_by,
        )

class AuditOperationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditOperationSerializer
    permission_classes = [AllowAny]

    queryset = (
        AuditOperation.objects
        .select_related(
            "performed_by",
            "reverses_operation",
        )
        .order_by("-performed_at")
    )

    @action(
        detail=True,
        methods=["post"],
        url_path="undo",
    )
    def undo(self, request, pk=None):
        operation = self.get_object()

        performed_by = request.user

        # Temporary development fallback.
        # Remove once real authentication is wired.
        if not performed_by.is_authenticated:
            performed_by = (
                get_user_model()
                .objects
                .filter(is_superuser=True)
                .first()
            )

        if performed_by is None:
            return Response(
                {
                    "detail":
                    "No authenticated user is available "
                    "to perform this undo."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = (
            request.data.get("reason")
            or f"Undo operation {operation.id}"
        )

        try:
            if operation.operation_type == "animal_move":
                undo_animal_move(
                    operation=operation,
                    performed_by=performed_by,
                    reason=reason,
                )

            elif operation.operation_type == "cage_move":
                undo_cage_move(
                    operation=operation,
                    performed_by=performed_by,
                    reason=reason,
                )

            else:
                return Response(
                    {
                        "detail":
                        "This operation type does not "
                        "support undo."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except ValidationError as exc:
            message = (
                exc.messages[0]
                if hasattr(exc, "messages")
                else str(exc)
            )

            return Response(
                {"detail": message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        operation.refresh_from_db()

        serializer = self.get_serializer(operation)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(
            request.user
        )

        return Response(serializer.data)