from django.db import transaction

from colony.models import (
    HusbandryEvent,
    HusbandryEventWeight,
    HusbandryEventTreatment,
)

@transaction.atomic
def correct_husbandry_event(
    *,
    original_event,
    recorded_by,
    event_datetime=None,
    notes=None,
    weight_grams=None,
    treatment_name=None,
    dose=None,
    route=None,
):
    original_event = (
        HusbandryEvent.objects
        .select_for_update()
        .get(pk=original_event.pk)
    )

    if HusbandryEvent.objects.filter(
        correction_of=original_event
    ).exists():
        raise ValueError(
            "This event has already been corrected."
        )       

    allowed_types = {
        HusbandryEvent.EventType.HEALTH_CHECK,
        HusbandryEvent.EventType.WEIGHT,
        HusbandryEvent.EventType.TREATMENT,
    }

    if original_event.event_type not in allowed_types:
        raise ValueError(
            "This event type cannot be corrected through "
            "the husbandry correction workflow."
        )

    corrected_event = HusbandryEvent.objects.create(
        event_type=original_event.event_type,
        animal=original_event.animal,
        cage=original_event.cage,
        litter=original_event.litter,
        event_datetime=(
            event_datetime
            if event_datetime is not None
            else original_event.event_datetime
        ),
        recorded_by=recorded_by,
        notes=(
            notes
            if notes is not None
            else original_event.notes
        ),
        metadata=original_event.metadata.copy(),
        correction_of=original_event,
    )

    if (
        original_event.event_type
        == HusbandryEvent.EventType.WEIGHT
    ):
        original_detail = (
            HusbandryEventWeight.objects
            .filter(event=original_event)
            .first()
        )

        corrected_weight = (
            weight_grams
            if weight_grams is not None
            else (
                original_detail.weight_grams
                if original_detail
                else None
            )
        )

        if corrected_weight is None:
            raise ValueError(
                "A weight value is required."
            )

        HusbandryEventWeight.objects.create(
            event=corrected_event,
            weight_grams=corrected_weight,
        )

    elif (
        original_event.event_type
        == HusbandryEvent.EventType.TREATMENT
    ):
        original_detail = (
            HusbandryEventTreatment.objects
            .filter(event=original_event)
            .first()
        )

        corrected_drug = (
            treatment_name
            if treatment_name is not None
            else (
                original_detail.drug_name
                if original_detail
                else ""
            )
        )

        corrected_dose = (
            dose
            if dose is not None
            else (
                original_detail.dose
                if original_detail
                else ""
            )
        )

        corrected_route = (
            route
            if route is not None
            else (
                original_detail.route
                if original_detail
                else ""
            )
        )

        if not corrected_drug:
            raise ValueError(
                "Treatment name is required."
            )

        HusbandryEventTreatment.objects.create(
            event=corrected_event,
            drug_name=corrected_drug,
            dose=corrected_dose,
            route=corrected_route,
        )

    return corrected_event
