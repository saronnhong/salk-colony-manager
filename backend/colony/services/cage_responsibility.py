from django.db import transaction
from django.utils import timezone

from colony.models import Cage, CageResponsibility
from django.db.models import Q


@transaction.atomic
def assign_cage_responsibility(
    *,
    cage: Cage,
    user,
    responsibility_type: str,
    assigned_by,
    valid_from=None,
    valid_to=None,
    notes="",
):
    if responsibility_type not in {
        CageResponsibility.ResponsibilityType.PRIMARY,
        CageResponsibility.ResponsibilityType.COVERAGE,
    }:
        raise ValueError(
            "Invalid responsibility type."
        )

    if cage.retired_at is not None:
        raise ValueError(
            "Cannot assign responsibility to a retired cage."
        )

    start = valid_from or timezone.now()

    if valid_to is not None and valid_to <= start:
        raise ValueError(
            "Responsibility end must be after the start time."
        )

    current_responsibilities = (
        CageResponsibility.objects
        .select_for_update()
        .filter(
            cage=cage,
            responsibility_type=responsibility_type,
            valid_from__lte=start,
        )
        .filter(
            Q(valid_to__isnull=True)
            | Q(valid_to__gt=start)
        )
    )

    for responsibility in current_responsibilities:
        responsibility.valid_to = start
        responsibility.save(
            update_fields=["valid_to"]
        )

    return CageResponsibility.objects.create(
        cage=cage,
        user=user,
        responsibility_type=responsibility_type,
        valid_from=start,
        valid_to=valid_to,
        assigned_by=assigned_by,
        notes=notes,
    )