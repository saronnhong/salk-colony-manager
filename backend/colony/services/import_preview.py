import csv
import hashlib
import io
from datetime import datetime

from django.db import transaction

from colony.models import (
    Cage,
    ImportBatch,
    ImportRow,
)


REQUIRED_COLUMNS = {
    "local_id",
    "sex",
    "date_of_birth",
    "species",
    "strain",
    "cage_code",
}


def validate_row(row):
    errors = {}

    local_id = row.get("local_id", "").strip()
    sex = row.get("sex", "").strip().upper()
    date_of_birth = row.get("date_of_birth", "").strip()
    species = row.get("species", "").strip()
    strain = row.get("strain", "").strip()
    cage_code = row.get("cage_code", "").strip()

    if not local_id:
        errors["local_id"] = "Local ID is required."

    if sex not in {"M", "F"}:
        errors["sex"] = "Sex must be M or F."

    if not date_of_birth:
        errors["date_of_birth"] = "Date of birth is required."
    else:
        try:
            datetime.strptime(
                date_of_birth,
                "%Y-%m-%d",
            )
        except ValueError:
            errors["date_of_birth"] = (
                "Date of birth must use YYYY-MM-DD."
            )

    if not species:
        errors["species"] = "Species is required."

    if not strain:
        errors["strain"] = "Strain is required."

    if not cage_code:
        errors["cage_code"] = "Cage code is required."
    elif not Cage.objects.filter(
        cage_code=cage_code,
        retired_at__isnull=True,
    ).exists():
        errors["cage_code"] = (
            f'Active cage "{cage_code}" was not found.'
        )

    return errors


@transaction.atomic
def preview_animal_import(
    *,
    uploaded_file,
    uploaded_by,
):
    raw_bytes = uploaded_file.read()

    file_hash = hashlib.sha256(
        raw_bytes,
    ).hexdigest()

    existing_committed_batch = ImportBatch.objects.filter(
        file_hash=file_hash,
        status__in=[
            ImportBatch.Status.COMMITTED,
            ImportBatch.Status.COMMITTED_WITH_ERRORS,
        ],
    ).first()

    if existing_committed_batch:
        raise ValueError(
            "This file has already been imported."
        )

    batch = ImportBatch.objects.create(
        uploaded_by=uploaded_by,
        filename=uploaded_file.name,
        file_hash=file_hash,
        status=ImportBatch.Status.UPLOADED,
    )

    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        batch.status = ImportBatch.Status.VALIDATION_FAILED
        batch.save(update_fields=["status"])

        raise ValueError(
            "CSV must be UTF-8 encoded."
        ) from exc

    reader = csv.DictReader(
        io.StringIO(text),
    )

    if reader.fieldnames is None:
        batch.status = ImportBatch.Status.VALIDATION_FAILED
        batch.save(update_fields=["status"])

        raise ValueError(
            "CSV does not contain a header row."
        )

    fieldnames = {
        name.strip()
        for name in reader.fieldnames
        if name
    }

    missing_columns = REQUIRED_COLUMNS - fieldnames

    if missing_columns:
        batch.status = ImportBatch.Status.VALIDATION_FAILED
        batch.save(update_fields=["status"])

        raise ValueError(
            "Missing required columns: "
            + ", ".join(
                sorted(missing_columns)
            )
        )

    has_errors = False

    for row_number, row in enumerate(
        reader,
        start=2,
    ):
        normalized_row = {
            key.strip(): (
                value.strip()
                if isinstance(value, str)
                else value
            )
            for key, value in row.items()
            if key is not None
        }

        errors = validate_row(
            normalized_row,
        )

        if errors:
            has_errors = True
            parse_status = (
                ImportRow.ParseStatus.INVALID
            )
        else:
            parse_status = (
                ImportRow.ParseStatus.VALID
            )

        ImportRow.objects.create(
            batch=batch,
            row_number=row_number,
            raw_data=normalized_row,
            parse_status=parse_status,
            validation_errors=errors or None,
        )

    batch.status = (
        ImportBatch.Status.VALIDATION_FAILED
        if has_errors
        else ImportBatch.Status.VALIDATED
    )

    batch.save(
        update_fields=["status"],
    )

    return batch