from django.db import transaction

from colony.models import (
    Animal,
    AnimalCageAssignment,
    AnimalLocalIdentifier,
    AuditLog,
    AuditOperation,
    HusbandryEvent,
    ImportBatch,
    ImportRow,
)


@transaction.atomic
def undo_animal_import(
    *,
    batch: ImportBatch,
    performed_by,
):
    batch = (
        ImportBatch.objects
        .select_for_update()
        .get(pk=batch.pk)
    )

    if batch.status not in [
        ImportBatch.Status.COMMITTED,
        ImportBatch.Status.COMMITTED_WITH_ERRORS,
    ]:
        raise ValueError(
            "Only a committed import can be undone."
        )

    original_operation = batch.audit_operation

    if original_operation is None:
        raise ValueError(
            "This import does not have an audit operation."
        )

    if original_operation.is_reversed:
        raise ValueError(
            "This import has already been undone."
        )

    #
    # Find exactly what the import created from the audit log.
    #
    animal_logs = AuditLog.objects.filter(
        operation=original_operation,
        table_name=Animal._meta.db_table,
        action=AuditLog.Action.INSERT,
    )

    assignment_logs = AuditLog.objects.filter(
        operation=original_operation,
        table_name=AnimalCageAssignment._meta.db_table,
        action=AuditLog.Action.INSERT,
    )

    identifier_logs = AuditLog.objects.filter(
        operation=original_operation,
        table_name=AnimalLocalIdentifier._meta.db_table,
        action=AuditLog.Action.INSERT,
    )

    animal_ids = [
        log.row_id
        for log in animal_logs
    ]

    assignment_ids = [
        log.row_id
        for log in assignment_logs
    ]

    identifier_ids = [
        log.row_id
        for log in identifier_logs
    ]

    animals = list(
        Animal.objects
        .select_for_update()
        .filter(pk__in=animal_ids)
    )

    assignments = list(
        AnimalCageAssignment.objects
        .select_for_update()
        .filter(pk__in=assignment_ids)
    )

    identifiers = list(
        AnimalLocalIdentifier.objects
        .select_for_update()
        .filter(pk__in=identifier_ids)
    )

    #
    # Safety checks.
    #
    # Undoing an import should only be allowed while the imported
    # records are still in the state created by that import.
    #

    if len(animals) != len(animal_ids):
        raise ValueError(
            "One or more imported animals no longer exist. "
            "The import cannot be safely undone."
        )

    if len(assignments) != len(assignment_ids):
        raise ValueError(
            "One or more imported cage assignments have changed "
            "or no longer exist."
        )

    if len(identifiers) != len(identifier_ids):
        raise ValueError(
            "One or more imported identifiers have changed "
            "or no longer exist."
        )

    #
    # If an imported assignment has been closed, the animal was
    # probably moved after import.
    #
    changed_assignments = [
        assignment
        for assignment in assignments
        if assignment.valid_to is not None
        or assignment.system_to is not None
    ]

    if changed_assignments:
        raise ValueError(
            "One or more imported animals were moved after the "
            "import. Undo is no longer safe."
        )

    #
    # Do not delete animals that have gained husbandry history.
    #
    if HusbandryEvent.objects.filter(
        animal_id__in=animal_ids,
    ).exists():
        raise ValueError(
            "One or more imported animals have husbandry events. "
            "Undo is no longer safe."
        )

    #
    # Check that no additional cage assignments were created.
    #
    all_assignment_ids = set(
        str(value)
        for value in AnimalCageAssignment.objects.filter(
            animal_id__in=animal_ids,
        ).values_list(
            "pk",
            flat=True,
        )
    )

    imported_assignment_ids = set(
        str(value)
        for value in assignment_ids
    )

    if all_assignment_ids != imported_assignment_ids:
        raise ValueError(
            "One or more imported animals have additional location "
            "history. Undo is no longer safe."
        )

    #
    # Check that no identifiers were added after import.
    #
    all_identifier_ids = set(
        str(value)
        for value in AnimalLocalIdentifier.objects.filter(
            animal_id__in=animal_ids,
        ).values_list(
            "pk",
            flat=True,
        )
    )

    imported_identifier_ids = set(
        str(value)
        for value in identifier_ids
    )

    if all_identifier_ids != imported_identifier_ids:
        raise ValueError(
            "One or more imported animals have additional identifiers. "
            "Undo is no longer safe."
        )

    #
    # Create the compensating audit operation BEFORE deleting records.
    #
    undo_operation = AuditOperation.objects.create(
        operation_type="animal_import_undo",
        performed_by=performed_by,
        reason=f"Undo animal import {batch.filename}",
        reverses_operation=original_operation,
        metadata={
            "import_batch_id": batch.pk,
            "filename": batch.filename,
            "original_operation_id": original_operation.pk,
            "animal_count": len(animals),
        },
    )

    #
    # Delete in FK-safe order.
    #

    for assignment in assignments:
        AuditLog.objects.create(
            operation=undo_operation,
            table_name=AnimalCageAssignment._meta.db_table,
            row_id=str(assignment.pk),
            action=AuditLog.Action.DELETE,
            old_values={
                "animal_id": str(assignment.animal.pk),
                "cage_id": str(assignment.cage.pk),
                "valid_from": assignment.valid_from.isoformat(),
                "valid_to": (
                    assignment.valid_to.isoformat()
                    if assignment.valid_to
                    else None
                ),
            },
            new_values=None,
        )

        assignment.delete()

    for identifier in identifiers:
        AuditLog.objects.create(
            operation=undo_operation,
            table_name=AnimalLocalIdentifier._meta.db_table,
            row_id=str(identifier.pk),
            action=AuditLog.Action.DELETE,
            old_values={
                "animal_id": str(identifier.animal.pk),
                "identifier_type": identifier.identifier_type,
                "value": identifier.value,
            },
            new_values=None,
        )

        identifier.delete()

    for animal in animals:
        AuditLog.objects.create(
            operation=undo_operation,
            table_name=Animal._meta.db_table,
            row_id=str(animal.pk),
            action=AuditLog.Action.DELETE,
            old_values={
                "animal_id": str(animal.pk),
                "sex": animal.sex,
                "date_of_birth": (
                    animal.date_of_birth.isoformat()
                    if animal.date_of_birth
                    else None
                ),
                "species": animal.species,
                "strain": str(animal.strain)
                if animal.strain
                else None,
            },
            new_values=None,
        )

        animal.delete()

    ImportRow.objects.filter(
        batch=batch,
        parse_status=ImportRow.ParseStatus.COMMITTED,
    ).update(
        parse_status=ImportRow.ParseStatus.UNDONE,
    )

    batch.status = ImportBatch.Status.UNDONE

    batch.save(
        update_fields=[
            "status",
        ],
    )

    return {
        "batch": batch,
        "undo_operation": undo_operation,
        "undone_count": len(animals),
    }