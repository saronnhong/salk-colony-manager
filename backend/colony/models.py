"""
Animal Colony Manager — Django models implementing the v2 data model.

App name assumed: `colony`. Requires PostgreSQL and the `btree_gist` extension
(enabled via migrations/0001_enable_btree_gist.py, which must be applied
before the migration that creates AnimalCageAssignment / CageRackPositionAssignment).

Two pieces of the design are NOT expressible as Django models and are handled
as raw SQL in migrations/0003_death_guard_triggers_and_views.py:
  1. The "no events after death" trigger (Postgres CHECK constraints can't
     reference other tables).
  2. The animal_current_location / cage_current_location views (§6 of the
     design doc) — modeled here as unmanaged models pointed at those views.

One manual step this file does NOT solve: keeping
AnimalLocalIdentifier.room in sync with the animal's current room is a
service-layer/signal responsibility, not a schema one — see the design doc.
"""

import uuid

from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators, RangeBoundary
from django.db import models
from django.db.models import CheckConstraint, F, Q, UniqueConstraint



class TsTzRange(models.Func):
    """PostgreSQL tstzrange expression used by exclusion constraints."""

    function = "TSTZRANGE"

    def __init__(self, *expressions, **extra):
        super().__init__(
            *expressions,
            output_field=DateTimeRangeField(),
            **extra,
        )


# ---------------------------------------------------------------------------
# Structure: rooms, racks, positions, cages
# ---------------------------------------------------------------------------

class Room(models.Model):
    name = models.CharField(max_length=100)
    building = models.CharField(max_length=100, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "room"

    def __str__(self):
        return self.name


class Rack(models.Model):
    room = models.ForeignKey(Room, on_delete=models.RESTRICT, related_name="racks")
    rack_code = models.CharField(max_length=50)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rack"

    def __str__(self):
        return f"{self.room.name} / {self.rack_code}"


class RackPosition(models.Model):
    rack = models.ForeignKey(Rack, on_delete=models.RESTRICT, related_name="positions")
    position_label = models.CharField(max_length=50)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "rack_position"
        constraints = [
            UniqueConstraint(
                fields=["rack", "position_label"],
                condition=Q(retired_at__isnull=True),
                name="rack_position_active_unique",
            ),
        ]

    def __str__(self):
        return f"{self.rack} / {self.position_label}"


class Strain(models.Model):
    """Stub table. Flagged in the design doc as a real gap in the original
    requirements — expand once real requirements are gathered; do not treat
    this as a finished genotype/strain model."""
    name = models.CharField(max_length=200, unique=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "strain"

    def __str__(self):
        return self.name


class Cage(models.Model):
    class CageType(models.TextChoices):
        STANDARD = "standard", "Standard"
        BREEDING = "breeding", "Breeding"
        ISOLATION = "isolation", "Isolation"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cage_code = models.CharField(max_length=50)
    cage_type = models.CharField(max_length=20, choices=CageType.choices, default=CageType.STANDARD)
    retired_at = models.DateTimeField(null=True, blank=True)
    retired_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cage"
        constraints = [
            UniqueConstraint(
                fields=["cage_code"],
                condition=Q(retired_at__isnull=True),
                name="cage_code_active_unique",
            ),
        ]

    def __str__(self):
        return self.cage_code


# ---------------------------------------------------------------------------
# Animal identity
# ---------------------------------------------------------------------------

class Animal(models.Model):
    class Sex(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        UNKNOWN = "unknown", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sex = models.CharField(max_length=10, choices=Sex.choices, default=Sex.UNKNOWN)
    date_of_birth = models.DateField(null=True, blank=True)
    species = models.CharField(max_length=100, default="Mus musculus")
    strain = models.ForeignKey(
        Strain, null=True, blank=True, on_delete=models.SET_NULL, related_name="animals"
    )
    origin_litter = models.ForeignKey(
        "Litter", null=True, blank=True, on_delete=models.RESTRICT, related_name="pups",
        help_text="Null if not born in-colony (e.g. purchased animal).",
    )
    retired_at = models.DateTimeField(null=True, blank=True)
    retired_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "animal"
        indexes = [
            models.Index(fields=["retired_at"]),
        ]

    def __str__(self):
        return str(self.id)

class AnimalLocalIdentifier(models.Model):
    class IdentifierType(models.TextChoices):
        EAR_TAG = "ear_tag", "Ear tag"
        EAR_PUNCH = "ear_punch", "Ear punch"
        TOE_NUMBER = "toe_number", "Toe number"
        OTHER = "other", "Other"

    animal = models.ForeignKey(
        Animal,
        on_delete=models.RESTRICT,
        related_name="local_identifiers",
    )

    identifier_type = models.CharField(
        max_length=20,
        choices=IdentifierType.choices,
    )

    value = models.CharField(max_length=50)

    assigned_date = models.DateField()

    retired_date = models.DateField(
        null=True,
        blank=True,
    )

    notes = models.TextField(blank=True)

    class Meta:
        db_table = "animal_local_identifier"

        indexes = [
            models.Index(
                fields=["identifier_type", "value"],
            ),
        ]

    def __str__(self):
        return f"{self.value} ({self.get_identifier_type_display()})"
    # def __str__(self):
    #     return self.value


# ---------------------------------------------------------------------------
# Temporal assignment tables — the core of the design.
# Bitemporal on purpose: valid_from/valid_to = when it was true in the world;
# system_from/system_to = when the database believed it. Most writes only
# ever touch valid_to (closing an open interval) and leave system_to null —
# system_to is populated only for genuine retroactive corrections. See the
# design doc §1 and §8 (Operations B, D, E) for the distinction.
# ---------------------------------------------------------------------------

class AnimalCageAssignment(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.RESTRICT, related_name="cage_assignments")
    cage = models.ForeignKey(Cage, on_delete=models.RESTRICT, related_name="animal_assignments")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    system_from = models.DateTimeField(auto_now_add=True)
    system_to = models.DateTimeField(null=True, blank=True)
    husbandry_event = models.ForeignKey(
        "HusbandryEvent", null=True, blank=True, on_delete=models.RESTRICT,
        related_name="cage_assignments",
    )
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")
    correction_of = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.RESTRICT, related_name="corrections",
    )
    reason = models.TextField(blank=True)

    class Meta:
        db_table = "animal_cage_assignment"
        constraints = [
            CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gt=F("valid_from")),
                name="animal_cage_assignment_valid_range_check",
            ),
            # DB-level guarantee that an animal can't be recorded in two
            # cages at overlapping times, among currently-believed rows.
            # This is the real backstop for Operation J (concurrent edits).
            ExclusionConstraint(
                name="no_animal_in_two_cages",
                expressions=[
                    ("animal", RangeOperators.EQUAL),
                    (TsTzRange("valid_from", "valid_to", RangeBoundary()), RangeOperators.OVERLAPS,)
                ],
                condition=Q(system_to__isnull=True),
            ),
        ]
        indexes = [
            models.Index(fields=["animal", "valid_from", "valid_to"]),
            models.Index(fields=["cage", "valid_from", "valid_to"]),
            models.Index(
                fields=["animal_id"],
                condition=Q(valid_to__isnull=True, system_to__isnull=True),
                name="animal_cage_current_idx",
            ),
        ]


class CageRackPositionAssignment(models.Model):
    cage = models.ForeignKey(Cage, on_delete=models.RESTRICT, related_name="position_assignments")
    rack_position = models.ForeignKey(RackPosition, on_delete=models.RESTRICT, related_name="cage_assignments")
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    system_from = models.DateTimeField(auto_now_add=True)
    system_to = models.DateTimeField(null=True, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")
    correction_of = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.RESTRICT, related_name="corrections",
    )
    reason = models.TextField(blank=True)

    class Meta:
        db_table = "cage_rack_position_assignment"
        constraints = [
            CheckConstraint(
                condition=Q(valid_to__isnull=True) | Q(valid_to__gt=F("valid_from")),
                name="cage_position_assignment_valid_range_check",
            ),
            ExclusionConstraint(
                name="no_cage_double_booked_position",
                expressions=[
                    ("rack_position", RangeOperators.EQUAL),
                    (TsTzRange("valid_from", "valid_to"), RangeOperators.OVERLAPS),
                ],
                condition=Q(system_to__isnull=True),
            ),
        ]
        indexes = [
            models.Index(fields=["cage", "valid_from", "valid_to"]),
            models.Index(fields=["rack_position", "valid_from", "valid_to"]),
            models.Index(
                fields=["cage"],
                condition=Q(valid_to__isnull=True, system_to__isnull=True),
                name="cage_position_current_idx",
            ),
        ]


# Unmanaged models backing the current-location views created in
# migrations/0003_death_guard_triggers_and_views.py. Use these for read
# queries instead of re-deriving "current cage" by hand every time.
class AnimalCurrentLocation(models.Model):
    animal = models.OneToOneField(
        Animal, primary_key=True, db_column="animal_id",
        on_delete=models.DO_NOTHING, related_name="current_location",
    )
    cage = models.ForeignKey(Cage, db_column="cage_id", on_delete=models.DO_NOTHING, related_name="+")
    valid_from = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "animal_current_location"


class CageCurrentLocation(models.Model):
    cage = models.OneToOneField(
        Cage, primary_key=True, db_column="cage_id",
        on_delete=models.DO_NOTHING, related_name="current_location",
    )
    rack_position = models.ForeignKey(
        RackPosition, db_column="rack_position_id", on_delete=models.DO_NOTHING, related_name="+",
    )
    valid_from = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "cage_current_location"


# ---------------------------------------------------------------------------
# Breeding
# ---------------------------------------------------------------------------

class BreedingUnit(models.Model):
    cage = models.ForeignKey(Cage, on_delete=models.RESTRICT, related_name="breeding_units")
    formed_date = models.DateField()
    dissolved_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "breeding_unit"


class BreedingUnitAnimal(models.Model):
    class Role(models.TextChoices):
        SIRE = "sire", "Sire"
        DAM = "dam", "Dam"

    breeding_unit = models.ForeignKey(BreedingUnit, on_delete=models.RESTRICT, related_name="members")
    animal = models.ForeignKey(Animal, on_delete=models.RESTRICT, related_name="breeding_memberships")
    role = models.CharField(max_length=10, choices=Role.choices)
    joined_date = models.DateField()
    removed_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "breeding_unit_animal"
        constraints = [
            UniqueConstraint(
                fields=["breeding_unit", "animal", "joined_date"],
                name="breeding_unit_animal_unique",
            ),
        ]


class Litter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    breeding_unit = models.ForeignKey(BreedingUnit, on_delete=models.RESTRICT, related_name="litters")
    birth_date = models.DateField()
    weaning_date = models.DateField(null=True, blank=True)
    number_born = models.PositiveIntegerField(null=True, blank=True)
    number_weaned = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "litter"
        constraints = [
            CheckConstraint(
                condition=Q(weaning_date__isnull=True) | Q(weaning_date__gte=F("birth_date")),
                name="litter_weaning_after_birth_check",
            ),
        ]


class LitterParent(models.Model):
    """Replaces litter.dam_id/sire_id — see design doc §5. Supports multiple
    candidate parents per litter (harem breeding) with per-candidate
    confidence, which a single dam_id column cannot represent."""

    class Role(models.TextChoices):
        DAM = "dam", "Dam"
        SIRE = "sire", "Sire"

    class Confidence(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        PRESUMED = "presumed", "Presumed"
        POSSIBLE = "possible", "Possible"

    litter = models.ForeignKey(Litter, on_delete=models.RESTRICT, related_name="parents")
    animal = models.ForeignKey(Animal, on_delete=models.RESTRICT, related_name="litters_parented")
    role = models.CharField(max_length=10, choices=Role.choices)
    confidence = models.CharField(max_length=10, choices=Confidence.choices, default=Confidence.PRESUMED)

    class Meta:
        db_table = "litter_parent"
        constraints = [
            UniqueConstraint(fields=["litter", "animal", "role"], name="litter_parent_unique"),
        ]


# ---------------------------------------------------------------------------
# Husbandry events — class-table inheritance: shared core + one detail
# table per event type + a JSONB escape hatch for rare/import-sourced fields.
# ---------------------------------------------------------------------------

class HusbandryEvent(models.Model):
    class EventType(models.TextChoices):
        INTAKE = "intake", "Intake"
        CAGE_CHANGE = "cage_change", "Cage change"
        HEALTH_CHECK = "health_check", "Health check"
        WEIGHT = "weight", "Weight"
        TREATMENT = "treatment", "Treatment"
        DEATH = "death", "Death"
        TRANSFER = "transfer", "Transfer"
        WEANING = "weaning", "Weaning"
        TAIL_SNIP = "tail_snip", "Tail snip"

    event_type = models.CharField(max_length=20, choices=EventType.choices)
    animal = models.ForeignKey(
        Animal, null=True, blank=True, on_delete=models.RESTRICT, related_name="husbandry_events",
    )
    cage = models.ForeignKey(
        Cage, null=True, blank=True, on_delete=models.RESTRICT, related_name="husbandry_events",
    )
    litter = models.ForeignKey(
        Litter, null=True, blank=True, on_delete=models.RESTRICT, related_name="husbandry_events",
    )
    event_datetime = models.DateTimeField()
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")
    notes = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "husbandry_event"
        indexes = [
            models.Index(fields=["animal", "event_datetime"]),
            models.Index(fields=["cage", "event_datetime"]),
            models.Index(fields=["event_type", "event_datetime"]),
        ]


class HusbandryEventWeight(models.Model):
    event = models.OneToOneField(
        HusbandryEvent, primary_key=True, on_delete=models.CASCADE, related_name="weight_detail",
    )
    weight_grams = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table = "husbandry_event_weight"
        constraints = [CheckConstraint(condition=Q(weight_grams__gt=0), name="weight_positive_check")]


class HusbandryEventHealthCheck(models.Model):
    event = models.OneToOneField(
        HusbandryEvent, primary_key=True, on_delete=models.CASCADE, related_name="health_check_detail",
    )
    body_condition_score = models.PositiveSmallIntegerField(null=True, blank=True)
    findings = models.TextField(blank=True)

    class Meta:
        db_table = "husbandry_event_health_check"


class HusbandryEventTreatment(models.Model):
    event = models.OneToOneField(
        HusbandryEvent, primary_key=True, on_delete=models.CASCADE, related_name="treatment_detail",
    )
    drug_name = models.CharField(max_length=200)
    dose = models.CharField(max_length=100, blank=True)
    route = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "husbandry_event_treatment"


class HusbandryEventDeath(models.Model):
    class Method(models.TextChoices):
        FOUND_DEAD = "found_dead", "Found dead"
        EUTHANASIA_SCHEDULED = "euthanasia_scheduled", "Euthanasia (scheduled)"
        EUTHANASIA_CLINICAL = "euthanasia_clinical", "Euthanasia (clinical)"

    event = models.OneToOneField(
        HusbandryEvent, primary_key=True, on_delete=models.CASCADE, related_name="death_detail",
    )
    cause = models.TextField(blank=True)
    method = models.CharField(max_length=30, choices=Method.choices)
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Veterinary sign-off, if applicable.",
    )

    class Meta:
        db_table = "husbandry_event_death"


class HusbandryEventTailSnip(models.Model):
    event = models.OneToOneField(
        HusbandryEvent, primary_key=True, on_delete=models.CASCADE, related_name="tail_snip_detail",
    )
    sent_to_lab = models.CharField(max_length=200, blank=True)
    result_status = models.CharField(max_length=30, blank=True)  # 'pending' / 'resulted' / ...
    result = models.TextField(blank=True)

    class Meta:
        db_table = "husbandry_event_tail_snip"


# ---------------------------------------------------------------------------
# Audit — audit_operation groups many audit_log rows into one reviewable,
# undoable user action. See design doc §2/§3.
# ---------------------------------------------------------------------------

class AuditOperation(models.Model):
    operation_type = models.CharField(max_length=50)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")
    performed_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    reverses_operation = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.RESTRICT, related_name="reversed_by_operations",
    )

    class Meta:
        db_table = "audit_operation"
        indexes = [models.Index(fields=["reverses_operation"])]

    # @property
    # def is_reversed(self) -> bool:
    #     return self.reversed_by_operations.exists()
    @property
    def is_reversed(self) -> bool:
        return AuditOperation.objects.filter(
            reverses_operation=self
        ).exists()


class AuditLog(models.Model):
    class Action(models.TextChoices):
        INSERT = "insert", "Insert"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    operation = models.ForeignKey(AuditOperation, on_delete=models.RESTRICT, related_name="log_entries")
    table_name = models.CharField(max_length=100)
    row_id = models.CharField(max_length=64)  # text, since PKs are a mix of UUID and bigint
    action = models.CharField(max_length=10, choices=Action.choices)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["operation"]),
            models.Index(fields=["table_name", "row_id", "created_at"]),
        ]


# ---------------------------------------------------------------------------
# CSV/XLSX import staging
# ---------------------------------------------------------------------------

class ImportBatch(models.Model):
    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        VALIDATED = "validated", "Validated"
        VALIDATION_FAILED = "validation_failed", "Validation failed"
        COMMITTED = "committed", "Committed"
        COMMITTED_WITH_ERRORS = "committed_with_errors", "Committed with errors"
        UNDONE = "undone", "Undone"

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    filename = models.CharField(max_length=255)
    file_hash = models.CharField(max_length=64, help_text="SHA-256 hex digest of the raw file bytes.")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.UPLOADED)
    audit_operation = models.ForeignKey(
        AuditOperation, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )

    class Meta:
        db_table = "import_batch"
        constraints = [
            # Blocks two *live* commits of identical content, without
            # permanently poisoning a hash once used (see design doc §4).
            UniqueConstraint(
                fields=["file_hash"],
                condition=Q(status__in=["committed", "committed_with_errors"]),
                name="import_batch_hash_committed_unique",
            ),
        ]


class ImportRow(models.Model):
    class ParseStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        VALID = "valid", "Valid"
        INVALID = "invalid", "Invalid"
        SKIPPED = "skipped", "Skipped"
        COMMITTED = "committed", "Committed"

    batch = models.ForeignKey(ImportBatch, on_delete=models.CASCADE, related_name="rows")
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField()
    parse_status = models.CharField(max_length=20, choices=ParseStatus.choices, default=ParseStatus.PENDING)
    validation_errors = models.JSONField(null=True, blank=True)
    matched_animal = models.ForeignKey(Animal, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_record_type = models.CharField(max_length=50, blank=True)
    created_record_id = models.CharField(
        max_length=64, blank=True,
        help_text="Traceability only — NOT the undo mechanism. Undo replays audit_log rows "
                   "under the batch's audit_operation instead.",
    )

    class Meta:
        db_table = "import_row"
        indexes = [models.Index(fields=["batch", "row_number"])]


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

class UserRole(models.Model):
    class Role(models.TextChoices):
        PI = "pi", "Principal Investigator"
        LAB_MANAGER = "lab_manager", "Lab Manager"
        RESEARCHER = "researcher", "Researcher"
        STUDENT = "student", "Student"
        VETERINARIAN = "veterinarian", "Facility Veterinarian"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="colony_roles")
    role = models.CharField(max_length=20, choices=Role.choices)
    scope_room = models.ForeignKey(
        Room, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
        help_text="Optional: restrict this role to a specific room.",
    )

    class Meta:
        db_table = "user_role"
        constraints = [
            UniqueConstraint(fields=["user", "role"],condition=Q(scope_room__isnull=True),name="user_role_global_unique",),
            UniqueConstraint(fields=["user", "role", "scope_room"],condition=Q(scope_room__isnull=False),name="user_role_room_unique",),
        ]