from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "colony",
            "0008_backfill_rack_room_assignments",
        ),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                CREATE VIEW rack_current_room AS
                SELECT
                    rack_id,
                    room_id,
                    valid_from
                FROM rack_room_assignment
                WHERE valid_to IS NULL
                  AND system_to IS NULL;
            """,
            reverse_sql="""
                DROP VIEW IF EXISTS rack_current_room;
            """,
        ),
    ]