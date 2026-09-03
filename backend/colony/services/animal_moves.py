from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from colony.models import (
    Animal,
    AnimalCageAssignment,
    AuditLog,
    AuditOperation,
    Cage,
    HusbandryEvent,
)


@transaction.atomic
def move_animal(
    *,
    animal: Animal,
    destination_cage: Cage,
    performed_by,
    moved_at=None,
    reason="",
):
    moved_at = moved_at or timezone.now()

    animal = (
        Animal.objects
        .select_for_update()
        .get(pk=animal.pk)
    )

    destination_cage = (
        Cage.objects
        .select_for_update()
        .get(pk=destination_cage.pk)
    )

    if animal.retired_at is not None:
        raise ValidationError(
            "A retired animal cannot be moved."
        )

    if destination_cage.retired_at is not None:
        raise ValidationError(
            "Cannot move an animal into a retired cage."
        )

    current_assignment = (
        AnimalCageAssignment.objects
        .select_for_update()
        .filter(
            animal=animal,
            valid_to__isnull=True,
            system_to__isnull=True,
        )
        .select_related("cage")
        .first()
    )

    if current_assignment is None:
        raise ValidationError(
            "Animal does not currently have a cage assignment."
        )

    if current_assignment.cage.pk == destination_cage.pk:
        raise ValidationError(
            "Animal is already assigned to this cage."
        )

    if moved_at <= current_assignment.valid_from:
        raise ValidationError(
            "Move time must be after the current assignment began."
        )

    operation = AuditOperation.objects.create(
        operation_type="animal_move",
        performed_by=performed_by,
        reason=reason,
        metadata={
            "animal_id": str(animal.pk),
            "source_cage_id": str(current_assignment.cage.pk),
            "destination_cage_id": str(destination_cage.pk),
            "moved_at": moved_at.isoformat(),
        },
    )

    transfer_event = HusbandryEvent.objects.create(
        event_type=HusbandryEvent.EventType.TRANSFER,
        animal=animal,
        cage=destination_cage,
        event_datetime=moved_at,
        recorded_by=performed_by,
        notes=reason,
        metadata={
            "source_cage_id": str(current_assignment.cage.pk),
            "destination_cage_id": str(destination_cage.pk),
        },
    )

    old_assignment_values = {
        "animal_id": str(animal.pk),
        "cage_id": str(current_assignment.cage.pk),
        "valid_from": current_assignment.valid_from.isoformat(),
        "valid_to": (
            current_assignment.valid_to.isoformat()
            if current_assignment.valid_to
            else None
        ),
    }

    current_assignment.valid_to = moved_at
    current_assignment.save(
        update_fields=["valid_to"]
    )

    AuditLog.objects.create(
        operation=operation,
        table_name="animal_cage_assignment",
        row_id=str(current_assignment.pk),
        action=AuditLog.Action.UPDATE,
        old_values=old_assignment_values,
        new_values={
            **old_assignment_values,
            "valid_to": moved_at.isoformat(),
        },
    )

    new_assignment = AnimalCageAssignment.objects.create(
        animal=animal,
        cage=destination_cage,
        valid_from=moved_at,
        recorded_by=performed_by,
        husbandry_event=transfer_event,
        reason=reason,
    )

    AuditLog.objects.create(
        operation=operation,
        table_name="animal_cage_assignment",
        row_id=str(new_assignment.pk),
        action=AuditLog.Action.INSERT,
        old_values=None,
        new_values={
            "animal_id": str(animal.pk),
            "cage_id": str(destination_cage.pk),
            "valid_from": moved_at.isoformat(),
            "valid_to": None,
        },
    )

    return new_assignment