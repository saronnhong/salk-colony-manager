from rest_framework import serializers
from django.utils import timezone
from django.db import models
from django.db.models import Q

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
    primary_owner = serializers.SerializerMethodField()
    current_coverage = serializers.SerializerMethodField()

    class Meta:
        model = Cage
        fields = [
            "id",
            "cage_code",
            "cage_type",
            "current_location",
            "animal_count",
            "primary_owner",
            "current_coverage",
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

    def get_primary_owner(self, obj):
        now = timezone.now()

        responsibility = (
            obj.responsibilities
            .filter(
                responsibility_type="primary",
                valid_from__lte=now,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=now)
            )
            .select_related("user")
            .first()
        )

        if not responsibility:
            return None

        user = responsibility.user

        return {
            "id": user.id,
            "name": user.get_full_name() or user.get_username(),
        }


    def get_current_coverage(self, obj):
        now = timezone.now()

        coverage = (
            obj.responsibilities
            .filter(
                responsibility_type="coverage",
                valid_from__lte=now,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=now)
            )
            .select_related("user")
            .order_by("valid_from")
            .first()
        )

        if not coverage:
            return None

        user = coverage.user

        return {
            "id": user.id,
            "name": user.get_full_name() or user.get_username(),
            "valid_from": coverage.valid_from,
            "valid_to": coverage.valid_to,
        }


class CageSerializer(serializers.ModelSerializer):
    current_location = serializers.SerializerMethodField()
    animals = serializers.SerializerMethodField()
    primary_owner = serializers.SerializerMethodField()
    current_coverage = serializers.SerializerMethodField()

    class Meta:
        model = Cage
        fields = [
            "id",
            "cage_code",
            "cage_type",
            "retired_at",
            "created_at",
            "current_location",
            "animals",
            "primary_owner",
            "current_coverage",
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
            .prefetch_related(
                "animal__local_identifiers"
            )
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

    def get_primary_owner(self, obj):
        now = timezone.now()

        responsibility = (
            obj.responsibilities
            .filter(
                responsibility_type="primary",
                valid_from__lte=now,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=now)
            )
            .select_related("user")
            .first()
        )

        if not responsibility:
            return None

        user = responsibility.user

        return {
            "id": user.id,
            "name": (
                user.get_full_name()
                or user.get_username()
            ),
        }

    def get_current_coverage(self, obj):
        now = timezone.now()

        coverage = (
            obj.responsibilities
            .filter(
                responsibility_type="coverage",
                valid_from__lte=now,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=now)
            )
            .select_related("user")
            .order_by("valid_from")
            .first()
        )

        if not coverage:
            return None

        user = coverage.user

        return {
            "id": user.id,
            "name": (
                user.get_full_name()
                or user.get_username()
            ),
            "valid_from": coverage.valid_from,
            "valid_to": coverage.valid_to,
        }

class AnimalMoveSerializer(serializers.Serializer):
    destination_cage_id = serializers.UUIDField()
    moved_at = serializers.DateTimeField(required=False)
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def validate_destination_cage_id(self, value):
        if not Cage.objects.filter(
            id=value,
            retired_at__isnull=True,
        ).exists():
            raise serializers.ValidationError(
                "Destination cage does not exist or is retired."
            )

        return value