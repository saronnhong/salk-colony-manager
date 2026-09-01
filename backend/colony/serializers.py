from rest_framework import serializers

from .models import (
    Animal,
    AnimalCurrentLocation,
    AnimalLocalIdentifier,
    Cage,
    CageCurrentLocation,
)


class AnimalSummarySerializer(serializers.ModelSerializer):
    identifier = serializers.SerializerMethodField()

    class Meta:
        model = Animal
        fields = [
            "id",
            "identifier",
            "sex",
            "date_of_birth",
            "species",
        ]

    def get_identifier(self, obj):
        identifier = (
            obj.local_identifiers
            .filter(retired_date__isnull=True)
            .order_by("assigned_date")
            .first()
        )

        return identifier.value if identifier else None


class AnimalSerializer(serializers.ModelSerializer):
    identifier = serializers.SerializerMethodField()
    current_location = serializers.SerializerMethodField()

    strain_name = serializers.CharField(
        source="strain.name",
        read_only=True,
    )

    class Meta:
        model = Animal
        fields = [
            "id",
            "identifier",
            "sex",
            "date_of_birth",
            "species",
            "strain_name",
            "retired_reason",
            "retired_at",
            "created_at",
            "current_location",
        ]

    def get_identifier(self, obj):
        identifier = (
            obj.local_identifiers
            .filter(retired_date__isnull=True)
            .order_by("assigned_date")
            .first()
        )

        return identifier.value if identifier else None

    def get_current_location(self, obj):
        try:
            location = obj.current_location
        except AnimalCurrentLocation.DoesNotExist:
            return None

        return {
            "cage_id": location.cage_id,
            "cage_code": location.cage.cage_code,
            "valid_from": location.valid_from,
        }


class CageSummarySerializer(serializers.ModelSerializer):
    current_location = serializers.SerializerMethodField()
    animal_count = serializers.SerializerMethodField()

    class Meta:
        model = Cage
        fields = [
            "id",
            "cage_code",
            "cage_type",
            "current_location",
            "animal_count",
        ]

    def get_current_location(self, obj):
        try:
            location = obj.current_location
        except CageCurrentLocation.DoesNotExist:
            return None

        position = location.rack_position

        return {
            "room": position.rack.room.name,
            "rack": position.rack.rack_code,
            "position": position.position_label,
            "valid_from": location.valid_from,
        }

    def get_animal_count(self, obj):
        return obj.animal_assignments.filter(
            valid_to__isnull=True,
            system_to__isnull=True,
        ).count()


class CageSerializer(serializers.ModelSerializer):
    current_location = serializers.SerializerMethodField()
    animals = serializers.SerializerMethodField()

    class Meta:
        model = Cage
        fields = [
            "id",
            "cage_code",
            "cage_type",
            "retired_reason",
            "retired_at",
            "created_at",
            "current_location",
            "animals",
        ]

    def get_current_location(self, obj):
        try:
            location = obj.current_location
        except CageCurrentLocation.DoesNotExist:
            return None

        position = location.rack_position

        return {
            "room": {
                "id": position.rack.room_id,
                "name": position.rack.room.name,
            },
            "rack": {
                "id": position.rack_id,
                "rack_code": position.rack.rack_code,
            },
            "position": {
                "id": position.id,
                "position_label": position.position_label,
            },
            "valid_from": location.valid_from,
        }

    def get_animals(self, obj):
        assignments = (
            obj.animal_assignments
            .filter(
                valid_to__isnull=True,
                system_to__isnull=True,
            )
            .select_related("animal")
            .prefetch_related("animal__local_identifiers")
            .order_by("valid_from")
        )

        animals = [
            assignment.animal
            for assignment in assignments
        ]

        return AnimalSummarySerializer(
            animals,
            many=True,
        ).data