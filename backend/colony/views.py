from django.shortcuts import render

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Animal, Cage
from .serializers import (
    AnimalSerializer,
    CageSerializer,
    CageSummarySerializer,
)


class AnimalViewSet(ReadOnlyModelViewSet):
    serializer_class = AnimalSerializer

    queryset = (
        # Animal.objects
        # .select_related(
        #     "strain",
        # )
        # .prefetch_related(
        #     "local_identifiers",
        # )
        # .order_by("-created_at")
        Animal.objects
        .select_related("strain")
        .prefetch_related("local_identifiers")
        .order_by("date_of_birth", "id")
    )
    


class CageViewSet(ReadOnlyModelViewSet):
    queryset = (
        Cage.objects
        .prefetch_related(
            "animal_assignments__animal",
            "animal_assignments__animal__local_identifiers",
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
