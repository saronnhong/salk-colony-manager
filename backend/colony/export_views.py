import csv

from django.http import HttpResponse

from rest_framework.views import APIView

from colony.models import (
    Animal,
    AnimalCurrentLocation,
    AnimalLocalIdentifier
)
from colony.permissions import HasColonyRole



class AnimalCensusCsvExportView(APIView):
    permission_classes = [HasColonyRole]

    def get(self, request):
        response = HttpResponse(
            content_type="text/csv",
        )

        response[
            "Content-Disposition"
        ] = 'attachment; filename="animal_census.csv"'

        writer = csv.writer(response)

        writer.writerow([
            "animal_id",
            "local_id",
            "sex",
            "date_of_birth",
            "species",
            "strain",
            "cage_code",
            "rack",
            "position",
            "room",
        ])

        animals = (
            Animal.objects
            .filter(
                retired_at__isnull=True,
            )
            .select_related(
                "strain",
                "current_location",
                "current_location__cage",
                "current_location__cage__current_location__rack_position",
                "current_location__cage__current_location__rack_position__rack",
                "current_location__cage__current_location__rack_position__rack__current_room",
                "current_location__cage__current_location__rack_position__rack__current_room__room",
            )
            .prefetch_related(
                "local_identifiers",
            )
            .order_by(
                "created_at",
            )
        )

        for animal in animals:
            current_location = getattr(
                animal,
                "current_location",
                None,
            )

            cage = (
                current_location.cage
                if current_location
                else None
            )

            cage_location = (
                getattr(
                    cage,
                    "current_location",
                    None,
                )
                if cage
                else None
            )

            position = (
                cage_location.rack_position
                if cage_location
                else None
            )

            rack = (
                position.rack
                if position
                else None
            )

            rack_room = (
                getattr(
                    rack,
                    "current_room",
                    None,
                )
                if rack
                else None
            )

            room = (
                rack_room.room
                if rack_room
                else None
            )

            identifier = (
                AnimalLocalIdentifier.objects
                .filter(
                    animal=animal,
                    retired_date__isnull=True,
                )
                .first()
            )

            writer.writerow([
                str(animal.pk),
                identifier.value
                if identifier
                else "",
                animal.sex,
                (
                    animal.date_of_birth.isoformat()
                    if animal.date_of_birth
                    else ""
                ),
                animal.species,
                str(animal.strain)
                if animal.strain
                else "",
                cage.cage_code
                if cage
                else "",
                rack.rack_code
                if rack
                else "",
                position.position_label
                if position
                else "",
                room.name
                if room
                else "",
            ])

        return response