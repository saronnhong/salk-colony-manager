from rest_framework import serializers
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q
from colony.services.death_events import record_death

from .models import (
    Animal,
    AnimalCurrentLocation,
    # AnimalLocalIdentifier,
    Cage,
    CageCurrentLocation,
    RackPosition,
    CageRackPositionAssignment,
    AnimalCageAssignment,
    RackCurrentRoom,
    HusbandryEvent,
    HusbandryEventWeight,
    HusbandryEventTreatment,
    AuditOperation,
    ImportBatch,
    ImportRow,
    CageResponsibility,
)
from django.contrib.auth import get_user_model

User = get_user_model()

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
        room = position.rack.current_room.room

        return {
            "room": room.name,
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
        room = position.rack.current_room.room

        return {
            "room": {
                "id": room.id,
                "name": room.name,
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

class CageMoveSerializer(serializers.Serializer):
    destination_rack_position_id = serializers.IntegerField()
    moved_at = serializers.DateTimeField(required=False)
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )

    def validate_destination_rack_position_id(self, value):
        if not RackPosition.objects.filter(
            id=value,
            retired_at__isnull=True,
        ).exists():
            raise serializers.ValidationError(
                "Destination rack position does not exist or is retired."
            )

        return value

class CageLocationHistorySerializer(serializers.ModelSerializer):
    rack = serializers.CharField(
        source="rack_position.rack.rack_code",
        read_only=True,
    )
    position = serializers.CharField(
        source="rack_position.position_label",
        read_only=True,
    )
    room = serializers.SerializerMethodField()

    class Meta:
        model = CageRackPositionAssignment
        fields = [
            "id",
            "room",
            "rack",
            "position",
            "valid_from",
            "valid_to",
            "system_from",
            "system_to",
            "reason",
        ]

    def get_room(self, obj):
        rack_assignment = (
            obj.rack_position.rack.room_assignments
            .filter(
                valid_from__lte=obj.valid_from,
                system_to__isnull=True,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=obj.valid_from)
            )
            .select_related("room")
            .order_by("-valid_from")
            .first()
        )

        return (
            rack_assignment.room.name
            if rack_assignment
            else None
        )

class AnimalLocationHistorySerializer(serializers.ModelSerializer):
    cage_code = serializers.CharField(
        source="cage.cage_code",
        read_only=True,
    )

    room = serializers.SerializerMethodField()
    rack = serializers.SerializerMethodField()
    position = serializers.SerializerMethodField()

    class Meta:
        model = AnimalCageAssignment
        fields = [
            "id",
            "cage_code",
            "room",
            "rack",
            "position",
            "valid_from",
            "valid_to",
            "system_from",
            "system_to",
            "reason",
        ]

    def _cage_location_at_assignment_start(self, obj):
        return (
            CageRackPositionAssignment.objects
            .filter(
                cage=obj.cage,
                valid_from__lte=obj.valid_from,
                system_to__isnull=True,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=obj.valid_from)
            )
            .select_related(
                "rack_position",
                "rack_position__rack",
            )
            .order_by("-valid_from")
            .first()
        )

    def _room_at_time(self, rack, when):
        return (
            rack.room_assignments
            .filter(
                valid_from__lte=when,
                system_to__isnull=True,
            )
            .filter(
                Q(valid_to__isnull=True)
                | Q(valid_to__gt=when)
            )
            .select_related("room")
            .order_by("-valid_from")
            .first()
        )

    def get_room(self, obj):
        cage_location = self._cage_location_at_assignment_start(obj)

        if cage_location is None:
            return None

        room_assignment = self._room_at_time(
            cage_location.rack_position.rack,
            obj.valid_from,
        )

        return (
            room_assignment.room.name
            if room_assignment
            else None
        )

    def get_rack(self, obj):
        cage_location = self._cage_location_at_assignment_start(obj)

        if cage_location is None:
            return None

        return cage_location.rack_position.rack.rack_code

    def get_position(self, obj):
        cage_location = self._cage_location_at_assignment_start(obj)

        if cage_location is None:
            return None

        return cage_location.rack_position.position_label

class RackPositionSummarySerializer(serializers.ModelSerializer):
    rack = serializers.CharField(
        source="rack.rack_code",
        read_only=True,
    )

    room = serializers.SerializerMethodField()
    occupied = serializers.SerializerMethodField()

    class Meta:
        model = RackPosition
        fields = [
            "id",
            "room",
            "rack",
            "position_label",
            "occupied",
        ]

    def get_room(self, obj):
        try:
            return obj.rack.current_room.room.name
        except RackCurrentRoom.DoesNotExist:
            return None

    def get_occupied(self, obj):
        return obj.cage_assignments.filter(
            valid_to__isnull=True,
            system_to__isnull=True,
        ).exists()

class HusbandryEventSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.SerializerMethodField()

    weight_grams = serializers.DecimalField(
        max_digits=7,
        decimal_places=2,
        required=False,
        write_only=True,
    )

    treatment_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    dose = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    route = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    death_cause = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    death_method = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    correction_of = serializers.PrimaryKeyRelatedField(
        read_only=True,
    )

    is_corrected = serializers.SerializerMethodField()                

    class Meta:
        model = HusbandryEvent
        fields = [
            "id",
            "event_type",
            "animal",
            "cage",
            "litter",
            "event_datetime",
            "recorded_at",
            "recorded_by",
            "recorded_by_name",
            "notes",
            "metadata",
            "weight_grams",
            "treatment_name",
            "dose",
            "route",
            "death_cause",
            "death_method",
            "correction_of",
            "is_corrected",
        ]
        read_only_fields = [
            "id",
            "recorded_at",
            "recorded_by",
            "recorded_by_name",
        ]

    def get_is_corrected(self, obj):
        return obj.corrections.exists()

    def get_recorded_by_name(self, obj):
        if not obj.recorded_by:
            return None

        full_name = obj.recorded_by.get_full_name().strip()
        return full_name or obj.recorded_by.username

    def validate(self, attrs):
        event_type = attrs.get("event_type")

        if event_type == HusbandryEvent.EventType.WEIGHT:
            if attrs.get("weight_grams") is None:
                raise serializers.ValidationError({
                    "weight_grams": "Weight is required for a weight event."
                })

        if event_type == HusbandryEvent.EventType.TREATMENT:
            if not attrs.get("treatment_name"):
                raise serializers.ValidationError({
                    "treatment_name": "Treatment name is required."
                })

        if event_type == HusbandryEvent.EventType.DEATH:
            if not attrs.get("death_cause"):
                raise serializers.ValidationError({
                    "death_cause": "Cause is required for a death event."
                })

            if not attrs.get("death_method"):
                raise serializers.ValidationError({
                    "death_method": "Method is required for a death event."
                })

        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        weight_grams = validated_data.pop(
            "weight_grams",
            None,
        )

        treatment_name = validated_data.pop(
            "treatment_name",
            "",
        )

        dose = validated_data.pop(
            "dose",
            "",
        )

        route = validated_data.pop(
            "route",
            "",
        )

        death_cause = validated_data.pop(
            "death_cause",
            "",
        )

        death_method = validated_data.pop(
            "death_method",
            "",
        )

        if (
            validated_data.get("event_type")
            == HusbandryEvent.EventType.DEATH
        ):
            animal = validated_data.get("animal")
            recorded_by = validated_data.get("recorded_by")
            event_datetime = validated_data.get("event_datetime")
            notes = validated_data.get("notes", "")

            return record_death(
                animal=animal,
                event_datetime=event_datetime,
                cause=death_cause,
                method=death_method,
                confirmed_by=recorded_by,
                recorded_by=recorded_by,
                notes=notes,
            )

        event = HusbandryEvent.objects.create(
            **validated_data
        )

        if (
            event.event_type
            == HusbandryEvent.EventType.WEIGHT
        ):
            HusbandryEventWeight.objects.create(
                event=event,
                weight_grams=weight_grams,
            )

        elif (
            event.event_type
            == HusbandryEvent.EventType.TREATMENT
        ):
            HusbandryEventTreatment.objects.create(
                event=event,
                drug_name=treatment_name,
                dose=dose,
                route=route,
            )

        return event

    def to_representation(self, instance):
        data = super().to_representation(instance)

        try:
            data["weight_grams"] = str(
                instance.weight_detail.weight_grams
            )
        except HusbandryEventWeight.DoesNotExist:
            data["weight_grams"] = None

        try:
            detail = instance.treatment_detail

            data["treatment"] = {
                "drug_name": detail.drug_name,
                "dose": detail.dose,
                "route": detail.route,
            }
        except HusbandryEventTreatment.DoesNotExist:
            data["treatment"] = None

        return data

class HusbandryEventCorrectionSerializer(serializers.Serializer):
    event_datetime = serializers.DateTimeField(
        required=False,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    weight_grams = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
    )

    treatment_name = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    dose = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    route = serializers.CharField(
        required=False,
        allow_blank=True,
    )

class AuditOperationSerializer(serializers.ModelSerializer):
    performed_by_name = serializers.SerializerMethodField()
    is_reversed = serializers.BooleanField(read_only=True)
    can_undo = serializers.SerializerMethodField()

    class Meta:
        model = AuditOperation
        fields = [
            "id",
            "operation_type",
            "performed_by",
            "performed_by_name",
            "performed_at",
            "reason",
            "metadata",
            "reverses_operation",
            "is_reversed",
            "can_undo",
        ]

    def get_performed_by_name(self, obj):
        user = obj.performed_by

        full_name = user.get_full_name()

        return full_name or user.username

    def get_can_undo(self, obj):
        if obj.is_reversed:
            return False

        if obj.reverses_operation_id is not None:
            return False

        metadata = obj.metadata

        if obj.operation_type == "animal_move":
            animal_id = metadata.get("animal_id")
            destination_cage_id = metadata.get(
                "destination_cage_id"
            )

            if not animal_id or not destination_cage_id:
                return False

            current_assignment = (
                AnimalCageAssignment.objects
                .filter(
                    animal_id=animal_id,
                    valid_to__isnull=True,
                    system_to__isnull=True,
                )
                .first()
            )

            if current_assignment is None:
                return False

            return str(
                current_assignment.cage.pk
            ) == str(destination_cage_id)

        if obj.operation_type == "cage_move":
            cage_id = metadata.get("cage_id")
            destination_position_id = metadata.get(
                "destination_rack_position_id"
            )

            if not cage_id or not destination_position_id:
                return False

            current_assignment = (
                CageRackPositionAssignment.objects
                .filter(
                    cage_id=cage_id,
                    valid_to__isnull=True,
                    system_to__isnull=True,
                )
                .select_related("rack_position")
                .first()
            )

            if current_assignment is None:
                return False

            return str(
                current_assignment.rack_position.pk
            ) == str(destination_position_id)

        return False

class CurrentUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()

class ImportRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportRow
        fields = [
            "id",
            "row_number",
            "raw_data",
            "parse_status",
            "validation_errors",
        ]


class ImportBatchSerializer(serializers.ModelSerializer):
    rows = ImportRowSerializer(
        many=True,
        read_only=True,
    )

    class Meta:
        model = ImportBatch
        fields = [
            "id",
            "filename",
            "uploaded_at",
            "status",
            "rows",
        ]

class ImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

# class CageResponsibilityAssignmentSerializer(
#     serializers.Serializer
# ):
#     user_id = serializers.IntegerField()

#     responsibility_type = serializers.ChoiceField(
#         choices=CageResponsibility.ResponsibilityType.choices
#     )

#     valid_from = serializers.DateTimeField(
#         required=False
#     )

#     valid_to = serializers.DateTimeField(
#         required=False,
#         allow_null=True,
#     )

#     notes = serializers.CharField(
#         required=False,
#         allow_blank=True,
#     )

#     def validate_user_id(self, value):
#         if not User.objects.filter(
#             id=value
#         ).exists():
#             raise serializers.ValidationError(
#                 "User not found."
#             )

#         return value

#     def validate(self, attrs):
#         valid_from = attrs.get("valid_from")
#         valid_to = attrs.get("valid_to")

#         if (
#             valid_from is not None
#             and valid_to is not None
#             and valid_to <= valid_from
#         ):
#             raise serializers.ValidationError(
#                 {
#                     "valid_to":
#                         "End time must be after start time."
#                 }
#             )

#         return attrs

class ColonyUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "name",
        ]

    def get_name(self, obj):
        return (
            obj.get_full_name()
            or obj.get_username()
        )

class CageResponsibilityAssignmentSerializer(
    serializers.Serializer
):
    user_id = serializers.IntegerField()

    responsibility_type = serializers.ChoiceField(
        choices=CageResponsibility.ResponsibilityType.choices
    )

    valid_from = serializers.DateTimeField(
        required=False
    )

    valid_to = serializers.DateTimeField(
        required=False,
        allow_null=True,
    )

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    def validate_user_id(self, value):
        if not User.objects.filter(
            id=value
        ).exists():
            raise serializers.ValidationError(
                "User not found."
            )

        return value

    def validate(self, attrs):
        valid_from = attrs.get("valid_from")
        valid_to = attrs.get("valid_to")

        if (
            valid_from is not None
            and valid_to is not None
            and valid_to <= valid_from
        ):
            raise serializers.ValidationError(
                {
                    "valid_to":
                        "End time must be after start time."
                }
            )

        return attrs