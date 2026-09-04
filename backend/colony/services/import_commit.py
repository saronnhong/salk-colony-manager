from datetime import datetime

from django.db import transaction
from django.utils import timezone

from colony.models import (
    Animal,
    AnimalCageAssignment,
    AnimalLocalIdentifier,
    AuditLog,
    AuditOperation,
    Cage,
    ImportBatch,
    ImportRow,
    Strain,
)


@transaction.atomic
def commit_animal_import(
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
        ImportBatch.Status.VALIDATED,
        ImportBatch.Status.VALIDATION_FAILED,
    ]:
        raise ValueError(
            "This import batch cannot be committed."
        )

    if batch.audit_operation is not None:
        raise ValueError(
            "This import batch has already been committed."
        )

    operation = AuditOperation.objects.create(
        operation_type="animal_import",
        performed_by=performed_by,
        reason=f"Imported animals from {batch.filename}",
        metadata={
            "import_batch_id": batch.pk,
            "filename": batch.filename,
            "file_hash": batch.file_hash,
        },
    )

    batch.audit_operation = operation

    rows = (
        ImportRow.objects
        .select_for_update()
        .filter(batch=batch)
        .order_by("row_number")
    )

    committed_count = 0
    skipped_count = 0

    for row in rows:
        if row.parse_status != ImportRow.ParseStatus.VALID:
            skipped_count += 1
            continue

        data = row.raw_data

        cage = Cage.objects.get(
            cage_code=data["cage_code"],
            retired_at__isnull=True,
        )

        date_of_birth = datetime.strptime(
            data["date_of_birth"],
            "%Y-%m-%d",
        ).date()

        strain = Strain.objects.filter(
            name=data["strain"],
        ).first()

        if strain is None:
            raise ValueError(
                f'Strain "{data["strain"]}" was not found.'
            )

        animal = Animal.objects.create(
            sex=data["sex"],
            date_of_birth=date_of_birth,
            species=data["species"],
            strain=strain,
        )

        identifier = AnimalLocalIdentifier.objects.create(
            animal=animal,
            identifier_type=(
                AnimalLocalIdentifier.IdentifierType.OTHER
            ),
            value=data["local_id"],
            assigned_date=date_of_birth,
            notes=f"Created from import batch {batch.pk}",
        )

        assignment = AnimalCageAssignment.objects.create(
            animal=animal,
            cage=cage,
            valid_from=timezone.now(),
            recorded_by=performed_by,
            reason=f"Imported from {batch.filename}",
        )

        AuditLog.objects.create(
            operation=operation,
            table_name=Animal._meta.db_table,
            row_id=str(animal.pk),
            action=AuditLog.Action.INSERT,
            old_values=None,
            new_values={
                "animal_id": str(animal.pk),
                "sex": animal.sex,
                "date_of_birth": date_of_birth.isoformat(),
                "species": animal.species,
                "strain": str(animal.strain),
            },
        )

        AuditLog.objects.create(
            operation=operation,
            table_name=AnimalCageAssignment._meta.db_table,
            row_id=str(assignment.pk),
            action=AuditLog.Action.INSERT,
            old_values=None,
            new_values={
                "animal_id": str(animal.pk),
                "cage_id": str(cage.pk),
                "valid_from": (
                    assignment.valid_from.isoformat()
                ),
                "valid_to": None,
            },
        )

        AuditLog.objects.create(
            operation=operation,
            table_name=AnimalLocalIdentifier._meta.db_table,
            row_id=str(identifier.pk),
            action=AuditLog.Action.INSERT,
            old_values=None,
            new_values={
                "animal_id": str(animal.pk),
                "identifier_type": identifier.identifier_type,
                "value": identifier.value,
            },
        )

        row.parse_status = (
            ImportRow.ParseStatus.COMMITTED
        )
        row.created_record_type = "animal"
        row.created_record_id = str(animal.pk)

        row.save(
            update_fields=[
                "parse_status",
                "created_record_type",
                "created_record_id",
            ],
        )

        committed_count += 1

    if skipped_count:
        batch.status = (
            ImportBatch.Status.COMMITTED_WITH_ERRORS
        )
    else:
        batch.status = ImportBatch.Status.COMMITTED

    batch.save(
        update_fields=[
            "status",
            "audit_operation",
        ],
    )

    return {
        "batch": batch,
        "committed_count": committed_count,
        "skipped_count": skipped_count,
    }