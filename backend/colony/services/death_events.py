from django.db import transaction

from colony.models import (
    Animal,
    AnimalCageAssignment,
    HusbandryEvent,
    HusbandryEventDeath,
)


@transaction.atomic
def record_death(
    *,
    animal,
    event_datetime,
    cause,
    method,
    confirmed_by,
    recorded_by,
    notes="",
):
    animal = (
        Animal.objects
        .select_for_update()
        .get(pk=animal.pk)
    )

    if animal.retired_at is not None:
        raise ValueError(
            "This animal is already retired."
        )

    current_assignment = (
        AnimalCageAssignment.objects
        .select_for_update()
        .filter(
            animal=animal,
            valid_to__isnull=True,
            system_to__isnull=True,
        )
        .first()
    )

    event = HusbandryEvent.objects.create(
        event_type=HusbandryEvent.EventType.DEATH,
        animal=animal,
        cage=(
            current_assignment.cage
            if current_assignment
            else None
        ),
        event_datetime=event_datetime,
        recorded_by=recorded_by,
        notes=notes,
    )

    HusbandryEventDeath.objects.create(
        event=event,
        cause=cause,
        method=method,
        confirmed_by=confirmed_by,
    )

    animal.retired_at = event_datetime
    animal.retired_reason = "death"

    animal.save(
        update_fields=[
            "retired_at",
            "retired_reason",
        ]
    )

    if current_assignment:
        current_assignment.valid_to = event_datetime

        current_assignment.save(
            update_fields=["valid_to"]
        )

    return event