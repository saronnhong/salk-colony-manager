from django.core.exceptions import ValidationError
from django.db import transaction

from colony.models import (
    Animal,
    AnimalCageAssignment,
    AuditOperation,
    Cage,
    CageRackPositionAssignment,
    RackPosition,
)

from colony.services.animal_moves import move_animal
from colony.services.cage_moves import move_cage


@transaction.atomic
def undo_animal_move(
    *,
    operation: AuditOperation,
    performed_by,
    reason="Undo animal move",
):
    operation = (
        AuditOperation.objects
        .select_for_update()
        .get(pk=operation.pk)
    )

    if operation.operation_type != "animal_move":
        raise ValidationError(
            "This operation is not an animal move."
        )

    if operation.is_reversed:
        raise ValidationError(
            "This operation has already been undone."
        )

    metadata = operation.metadata

    animal_id = metadata.get("animal_id")
    source_cage_id = metadata.get("source_cage_id")
    destination_cage_id = metadata.get(
        "destination_cage_id"
    )

    if not all([
        animal_id,
        source_cage_id,
        destination_cage_id,
    ]):
        raise ValidationError(
            "The original move does not contain enough "
            "information to undo it."
        )

    animal = (
        Animal.objects
        .select_for_update()
        .get(pk=animal_id)
    )

    source_cage = Cage.objects.get(
        pk=source_cage_id
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
            "The animal no longer has a current cage assignment."
        )

    if str(current_assignment.cage.pk) != str(
        destination_cage_id
    ):
        raise ValidationError(
            "This move cannot be undone because the animal "
            "has moved again since the original operation."
        )

    return move_animal(
        animal=animal,
        destination_cage=source_cage,
        performed_by=performed_by,
        reason=reason,
        reverses_operation=operation,
    )

@transaction.atomic
def undo_cage_move(
    *,
    operation: AuditOperation,
    performed_by,
    reason="Undo cage move",
):
    operation = (
        AuditOperation.objects
        .select_for_update()
        .get(pk=operation.pk)
    )

    if operation.operation_type != "cage_move":
        raise ValidationError(
            "This operation is not a cage move."
        )

    if operation.is_reversed:
        raise ValidationError(
            "This operation has already been undone."
        )

    metadata = operation.metadata

    cage_id = metadata.get("cage_id")
    source_position_id = metadata.get(
        "source_rack_position_id"
    )
    destination_position_id = metadata.get(
        "destination_rack_position_id"
    )

    if not all([
        cage_id,
        source_position_id,
        destination_position_id,
    ]):
        raise ValidationError(
            "The original move does not contain enough "
            "information to undo it."
        )

    cage = (
        Cage.objects
        .select_for_update()
        .get(pk=cage_id)
    )

    source_position = (
        RackPosition.objects
        .select_for_update()
        .get(pk=source_position_id)
    )

    current_assignment = (
        CageRackPositionAssignment.objects
        .select_for_update()
        .filter(
            cage=cage,
            valid_to__isnull=True,
            system_to__isnull=True,
        )
        .select_related("rack_position")
        .first()
    )

    if current_assignment is None:
        raise ValidationError(
            "The cage no longer has a current rack "
            "position assignment."
        )

    if str(current_assignment.rack_position.pk) != str(
        destination_position_id
    ):
        raise ValidationError(
            "This move cannot be undone because the cage "
            "has moved again since the original operation."
        )

    source_occupied = (
        CageRackPositionAssignment.objects
        .select_for_update()
        .filter(
            rack_position=source_position,
            valid_to__isnull=True,
            system_to__isnull=True,
        )
        .exclude(cage=cage)
        .exists()
    )

    if source_occupied:
        raise ValidationError(
            "This move cannot be undone because the "
            "original rack position is now occupied."
        )

    return move_cage(
        cage=cage,
        destination_position=source_position,
        performed_by=performed_by,
        reason=reason,
        reverses_operation=operation,
    )