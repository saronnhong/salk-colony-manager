from django.shortcuts import render

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated

from .models import Animal, Cage
from .serializers import (
    AnimalMoveSerializer,
    AnimalSerializer,
    CageSerializer,
    CageSummarySerializer,
)

from .services.animal_moves import move_animal
from rest_framework import status


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
        permission_classes=[IsAuthenticated],
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

        try:
            move_animal(
                animal=animal,
                destination_cage=destination_cage,
                performed_by=request.user,
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
    


class CageViewSet(ReadOnlyModelViewSet):
    queryset = (
        Cage.objects
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
