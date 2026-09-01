from django.db import migrations

# --- Death guard: no cage assignments or husbandry events for an animal
# dated after its recorded death. Compares event_datetime, not recorded_at,
# so a late-entered health check dated *before* the death is still allowed.
# Postgres CHECK constraints can't reference other tables, so this has to
# be a trigger. See design doc §8, Operation F.

CREATE_CAGE_ASSIGNMENT_GUARD = """
CREATE OR REPLACE FUNCTION reject_cage_assignment_after_death() RETURNS TRIGGER AS $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM husbandry_event he
    JOIN husbandry_event_death hed ON hed.event_id = he.id
    WHERE he.animal_id = NEW.animal_id AND he.event_datetime <= NEW.valid_from
  ) THEN
    RAISE EXCEPTION 'Animal % has a recorded death on or before this assignment''s valid_from', NEW.animal_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reject_cage_assignment_after_death
BEFORE INSERT ON animal_cage_assignment
FOR EACH ROW EXECUTE FUNCTION reject_cage_assignment_after_death();
"""

DROP_CAGE_ASSIGNMENT_GUARD = """
DROP TRIGGER IF EXISTS trg_reject_cage_assignment_after_death ON animal_cage_assignment;
DROP FUNCTION IF EXISTS reject_cage_assignment_after_death() CASCADE;
"""

CREATE_HUSBANDRY_EVENT_GUARD = """
CREATE OR REPLACE FUNCTION reject_husbandry_event_after_death() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.animal_id IS NOT NULL AND NEW.event_type <> 'death' AND EXISTS (
    SELECT 1 FROM husbandry_event he
    JOIN husbandry_event_death hed ON hed.event_id = he.id
    WHERE he.animal_id = NEW.animal_id AND he.event_datetime <= NEW.event_datetime
  ) THEN
    RAISE EXCEPTION 'Animal % has a recorded death on or before this event''s event_datetime', NEW.animal_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reject_husbandry_event_after_death
BEFORE INSERT ON husbandry_event
FOR EACH ROW EXECUTE FUNCTION reject_husbandry_event_after_death();
"""

DROP_HUSBANDRY_EVENT_GUARD = """
DROP TRIGGER IF EXISTS trg_reject_husbandry_event_after_death ON husbandry_event;
DROP FUNCTION IF EXISTS reject_husbandry_event_after_death() CASCADE;
"""

# --- Current-location views (design doc §6): "current belief" reads,
# backed by the partial indexes already declared on the assignment models.
# No trigger-maintained cache columns — the view IS the source of truth,
# just read a different way.

CREATE_VIEWS = """
CREATE VIEW animal_current_location AS
SELECT DISTINCT ON (animal_id) animal_id, cage_id, valid_from
FROM animal_cage_assignment
WHERE valid_to IS NULL AND system_to IS NULL
ORDER BY animal_id, valid_from DESC;

CREATE VIEW cage_current_location AS
SELECT DISTINCT ON (cage_id) cage_id, rack_position_id, valid_from
FROM cage_rack_position_assignment
WHERE valid_to IS NULL AND system_to IS NULL
ORDER BY cage_id, valid_from DESC;
"""

DROP_VIEWS = """
DROP VIEW IF EXISTS animal_current_location;
DROP VIEW IF EXISTS cage_current_location;
"""


class Migration(migrations.Migration):
    # Adjust to your actual initial migration's name once generated via
    # `makemigrations` (referred to as 0002_initial in the models.py docstring).
    dependencies = [
        ("colony", "0002_initial"),
    ]

    operations = [
        migrations.RunSQL(CREATE_CAGE_ASSIGNMENT_GUARD, reverse_sql=DROP_CAGE_ASSIGNMENT_GUARD),
        migrations.RunSQL(CREATE_HUSBANDRY_EVENT_GUARD, reverse_sql=DROP_HUSBANDRY_EVENT_GUARD),
        migrations.RunSQL(CREATE_VIEWS, reverse_sql=DROP_VIEWS),
    ]
