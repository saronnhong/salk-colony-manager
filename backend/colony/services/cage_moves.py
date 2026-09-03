from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from colony.models import (
    AuditLog,
    AuditOperation,
    Cage,
    CageRackPositionAssignment,
    RackPosition,
)


@transaction.atomic
def move_cage(
    *,
    cage,
    destination_position,
    performed_by,
    moved_at=None,
    reason="",
):
    moved_at = moved_at or timezone.now()

    # Lock the cage itself so two requests cannot move the same cage
    # concurrently.
    cage = (
        Cage.objects
        .select_for_update()
        .get(pk=cage.pk)
    )

    # Lock the destination position so another transaction cannot place
    # a different cage there while this move is being processed.
    destination_position = (
        RackPosition.objects
        .select_for_update()
        .select_related("rack")
        .get(pk=destination_position.pk)
    )

    if cage.retired_at is not None:
        raise ValidationError(
            "A retired cage cannot be moved."
        )

    if destination_position.retired_at is not None:
        raise ValidationError(
            "Cannot move a cage into a retired rack position."
        )

    if destination_position.rack.retired_at is not None:
        raise ValidationError(
            "Cannot move a cage onto a retired rack."
        )

    current_assignment = (
        CageRackPositionAssignment.objects
        .select_for_update()
        .filter(
            cage=cage,
            valid_to__isnull=True,
            system_to__isnull=True,
        )
        .select_related(
            "rack_position",
            "rack_position__rack",
        )
        .first()
    )

    if current_assignment is None:
        raise ValidationError(
            "Cage does not currently have a rack position assignment."
        )

    if current_assignment.rack_position.pk == destination_position.pk:
        raise ValidationError(
            "Cage is already assigned to this rack position."
        )

    if moved_at <= current_assignment.valid_from:
        raise ValidationError(
            "Move time must be after the current assignment began."
        )

    # Give a friendly application-level error before PostgreSQL's
    # exclusion constraint becomes the final concurrency backstop.
    destination_occupied = (
        CageRackPositionAssignment.objects
        .select_for_update()
        .filter(
            rack_position=destination_position,
            valid_to__isnull=True,
            system_to__isnull=True,
        )
        .exclude(cage=cage)
        .exists()
    )

    if destination_occupied:
        raise ValidationError(
            "Destination rack position is already occupied."
        )

    operation = AuditOperation.objects.create(
        operation_type="cage_move",
        performed_by=performed_by,
        reason=reason,
        metadata={
            "cage_id": str(cage.id),
            "source_rack_position_id": current_assignment.rack_position.pk,
            "destination_rack_position_id": destination_position.pk,
            "moved_at": moved_at.isoformat(),
        },
    )

    old_assignment_values = {
        "cage_id": str(current_assignment.cage.pk),
        "rack_position_id": current_assignment.rack_position.pk,
        "valid_from": current_assignment.valid_from.isoformat(),
        "valid_to": (
            current_assignment.valid_to.isoformat()
            if current_assignment.valid_to
            else None
        ),
    }

    current_assignment.valid_to = moved_at
    current_assignment.save(
        update_fields=["valid_to"],
    )

    AuditLog.objects.create(
        operation=operation,
        table_name="cage_rack_position_assignment",
        row_id=str(current_assignment.pk),
        action=AuditLog.Action.UPDATE,
        old_values=old_assignment_values,
        new_values={
            **old_assignment_values,
            "valid_to": moved_at.isoformat(),
        },
    )

    new_assignment = CageRackPositionAssignment.objects.create(
        cage=cage,
        rack_position=destination_position,
        valid_from=moved_at,
        recorded_by=performed_by,
        reason=reason,
    )

    AuditLog.objects.create(
        operation=operation,
        table_name="cage_rack_position_assignment",
        row_id=str(new_assignment.pk),
        action=AuditLog.Action.INSERT,
        old_values=None,
        new_values={
            "cage_id": str(cage.id),
            "rack_position_id": destination_position.pk,
            "valid_from": moved_at.isoformat(),
            "valid_to": None,
        },
    )

    return new_assignment