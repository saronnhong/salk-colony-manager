from datetime import datetime, timezone

from django.db import migrations


def backfill_rack_rooms(apps, schema_editor):
    Rack = apps.get_model("colony", "Rack")
    RackRoomAssignment = apps.get_model(
        "colony",
        "RackRoomAssignment",
    )
    User = apps.get_model(
        "auth",
        "User",
    )

    racks_to_backfill = Rack.objects.exclude(room_id__isnull=True)

    # Fresh databases have no legacy rack-room data to migrate.
    if not racks_to_backfill.exists():
        return

    user = (
        User.objects
        .filter(is_superuser=True)
        .first()
    )

    if user is None:
        raise RuntimeError(
            "A superuser is required to backfill existing rack room assignments."
        )

    valid_from = datetime(
        2026,
        8,
        25,
        8,
        0,
        tzinfo=timezone.utc,
    )

    for rack in racks_to_backfill:
        RackRoomAssignment.objects.get_or_create(
            rack_id=rack.id,
            room_id=rack.room_id,
            valid_from=valid_from,
            defaults={
                "recorded_by_id": user.id,
                "reason": "Initial room assignment migration",
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            "colony",
            "0007_rackroomassignment",
        ),
    ]

    operations = [
        migrations.RunPython(
            backfill_rack_rooms,
            migrations.RunPython.noop,
        ),
    ]