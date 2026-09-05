import uuid
from datetime import UTC, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from colony.models import (
    Animal,
    AnimalCageAssignment,
    AnimalLocalIdentifier,
    Cage,
    CageRackPositionAssignment,
    CageResponsibility,
    Rack,
    RackPosition,
    RackRoomAssignment,
    Room,
    Strain,
    HusbandryEvent,
    HusbandryEventWeight,
    HusbandryEventTreatment,
)
from decimal import Decimal


User = get_user_model()

DEMO_NAMESPACE = uuid.UUID(
    "0c267b2f-8569-4a42-b933-a64569ce0562"
)

ASSIGNMENT_START = datetime(
    2026,
    8,
    1,
    12,
    0,
    tzinfo=UTC,
)

HISTORY_START = datetime(
    2026,
    7,
    15,
    12,
    0,
    tzinfo=UTC,
)

EVENT_BASE = datetime(
    2026,
    9,
    3,
    16,
    0,
    tzinfo=UTC,
)

COVERAGE_START = datetime(
    2026,
    9,
    1,
    12,
    0,
    tzinfo=UTC,
)

COVERAGE_END = datetime(
    2026,
    9,
    10,
    12,
    0,
    tzinfo=UTC,
)


class Command(BaseCommand):
    help = (
        "Create a realistic, deterministic demo animal colony."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            "Seeding demo colony..."
        )

        assigned_by = self.get_assigned_by_user()

        strains = self.create_strains()

        rooms = self.create_rooms()

        racks = self.create_racks(
            rooms=rooms,
            assigned_by=assigned_by,
        )

        positions = self.create_positions(
            racks=racks,
        )

        responsibility_users = (
            self.create_responsibility_users()
        )

        cages = self.create_cages(
            positions=positions,
            assigned_by=assigned_by,
        )

        self.create_animals(
            cages=cages,
            strains=strains,
            assigned_by=assigned_by,
        )

        self.create_responsibilities(
            cages=cages,
            users=responsibility_users,
            assigned_by=assigned_by,
        )

        self.create_historical_animal_moves(
            cages=cages,
            assigned_by=assigned_by,
        )

        self.create_historical_cage_moves(
            assigned_by=assigned_by,
        )

        self.create_husbandry_events(
            cages=cages,
            assigned_by=assigned_by,
        )

        self.create_demo_deaths(
            assigned_by=assigned_by,
        )         

        self.print_summary()

    def create_demo_deaths(
        self,
        *,
        assigned_by,
    ):
        death_numbers = [
            341,
            342,
            343,
            344,
            345,
            346,
        ]

        for offset, animal_number in enumerate(
            death_numbers
        ):
            animal_id = uuid.uuid5(
                DEMO_NAMESPACE,
                f"demo-animal-{animal_number:04d}",
            )

            animal = Animal.objects.get(
                id=animal_id
            )

            death_time = (
                EVENT_BASE
                - timedelta(
                    days=3 + offset
                )
            )

            death_event, _ = (
                HusbandryEvent.objects
                .get_or_create(
                    event_type=(
                        HusbandryEvent
                        .EventType
                        .DEATH
                    ),
                    animal=animal,
                    event_datetime=death_time,
                    notes=(
                        "Demo colony death record"
                    ),
                    defaults={
                        "recorded_by":
                            assigned_by,
                        "metadata": {
                            "cause":
                                "Natural / endpoint",
                        },
                    },
                )
            )

            if animal.retired_at is None:
                current_assignment = (
                    AnimalCageAssignment.objects
                    .filter(
                        animal=animal,
                        valid_to__isnull=True,
                        system_to__isnull=True,
                    )
                    .first()
                )

                if (
                    current_assignment is not None
                    and
                    current_assignment.valid_from
                    <= death_time
                ):
                    current_assignment.valid_to = (
                        death_time
                    )

                    current_assignment.save(
                        update_fields=[
                            "valid_to",
                        ]
                    )

                    animal.retired_at = death_time
                    animal.retired_reason = (
                        "Death recorded in demo data"
                    )

                    animal.save(
                        update_fields=[
                            "retired_at",
                            "retired_reason",
                            "updated_at",
                        ]
                    )
                    
    def create_husbandry_events(
        self,
        *,
        cages,
        assigned_by,
    ):
        #
        # Weight measurements
        #
        for animal_number in range(
            1,
            81,
            4,
        ):
            animal_id = uuid.uuid5(
                DEMO_NAMESPACE,
                f"demo-animal-{animal_number:04d}",
            )

            animal = Animal.objects.get(
                id=animal_id
            )

            event_time = (
                EVENT_BASE
                - timedelta(
                    days=animal_number % 7
                )
            )

            event, _ = (
                HusbandryEvent.objects
                .get_or_create(
                    event_type=(
                        HusbandryEvent
                        .EventType
                        .WEIGHT
                    ),
                    animal=animal,
                    event_datetime=event_time,
                    notes="Demo routine weight",
                    defaults={
                        "recorded_by":
                            assigned_by,
                    },
                )
            )

            weight = Decimal(
                str(
                    19
                    + (
                        animal_number
                        % 12
                    )
                    + 0.5
                )
            )

            (
                HusbandryEventWeight.objects
                .get_or_create(
                    event=event,
                    defaults={
                        "weight_grams":
                            weight,
                    },
                )
            )

        #
        # Cage-level health checks
        #
        for index in range(
            0,
            len(cages),
            6,
        ):
            cage = cages[index]

            event_time = (
                EVENT_BASE
                - timedelta(
                    days=index % 5,
                    hours=2,
                )
            )

            (
                HusbandryEvent.objects
                .get_or_create(
                    event_type=(
                        HusbandryEvent
                        .EventType
                        .HEALTH_CHECK
                    ),
                    cage=cage,
                    event_datetime=event_time,
                    notes=(
                        "Demo routine health check: "
                        "animals active, coat normal."
                    ),
                    defaults={
                        "recorded_by":
                            assigned_by,
                    },
                )
            )

        #
        # Treatments
        #
        treatment_specs = [
            (
                102,
                "Topical antibiotic",
                "Small topical amount",
                "topical",
            ),
            (
                166,
                "Saline",
                "0.5 mL",
                "subcutaneous",
            ),
            (
                230,
                "Supportive fluid",
                "0.5 mL",
                "subcutaneous",
            ),
        ]

        for (
            animal_number,
            drug_name,
            dose,
            route,
        ) in treatment_specs:
            animal_id = uuid.uuid5(
                DEMO_NAMESPACE,
                f"demo-animal-{animal_number:04d}",
            )

            animal = Animal.objects.get(
                id=animal_id
            )

            event_time = (
                EVENT_BASE
                - timedelta(days=2)
            )

            event, _ = (
                HusbandryEvent.objects
                .get_or_create(
                    event_type=(
                        HusbandryEvent
                        .EventType
                        .TREATMENT
                    ),
                    animal=animal,
                    event_datetime=event_time,
                    notes=(
                        "Demo treatment event"
                    ),
                    defaults={
                        "recorded_by":
                            assigned_by,
                    },
                )
            )

            (
                HusbandryEventTreatment.objects
                .get_or_create(
                    event=event,
                    defaults={
                        "drug_name":
                            drug_name,
                        "dose":
                            dose,
                        "route":
                            route,
                    },
                )
            )
            
    def create_historical_cage_moves(
        self,
        *,
        assigned_by,
    ):
        move_specs = [
            ("D071", "Rack F", "11"),
            ("D072", "Rack F", "12"),
            ("D073", "Rack F", "13"),
            ("D074", "Rack F", "14"),
            ("D075", "Rack F", "15"),
        ]

        for (
            cage_code,
            old_rack_code,
            old_position_label,
        ) in move_specs:
            cage = Cage.objects.get(
                cage_code=cage_code
            )

            current_assignment = (
                CageRackPositionAssignment.objects
                .filter(
                    cage=cage,
                    valid_to__isnull=True,
                    system_to__isnull=True,
                )
                .first()
            )

            if current_assignment is None:
                continue

            if (
                current_assignment.valid_from
                != ASSIGNMENT_START
            ):
                continue

            old_position = (
                RackPosition.objects.get(
                    rack__rack_code=old_rack_code,
                    position_label=old_position_label,
                )
            )

            history_exists = (
                CageRackPositionAssignment.objects
                .filter(
                    cage=cage,
                    valid_from=HISTORY_START,
                    valid_to=ASSIGNMENT_START,
                )
                .exists()
            )

            if history_exists:
                continue

            CageRackPositionAssignment.objects.create(
                cage=cage,
                rack_position=old_position,
                valid_from=HISTORY_START,
                valid_to=ASSIGNMENT_START,
                recorded_by=assigned_by,
                reason=(
                    "Demo historical cage location"
                ),
            )
            
    def create_historical_animal_moves(
        self,
        *,
        cages,
        assigned_by,
    ):
        move_specs = [
            # animal number, previous cage code
            (41, "D015"),
            (77, "D025"),
            (113, "D035"),
            (149, "D045"),
            (185, "D055"),
            (221, "D065"),
        ]

        cage_by_code = {
            cage.cage_code: cage
            for cage in cages
        }

        for animal_number, previous_cage_code in move_specs:
            animal_id = uuid.uuid5(
                DEMO_NAMESPACE,
                f"demo-animal-{animal_number:04d}",
            )

            animal = Animal.objects.get(
                id=animal_id
            )

            previous_cage = cage_by_code[
                previous_cage_code
            ]

            current_assignment = (
                AnimalCageAssignment.objects
                .filter(
                    animal=animal,
                    valid_to__isnull=True,
                    system_to__isnull=True,
                )
                .first()
            )

            if current_assignment is None:
                continue

            # Only create history when the current assignment
            # starts at our deterministic initial census time.
            if (
                current_assignment.valid_from
                != ASSIGNMENT_START
            ):
                continue

            history_exists = (
                AnimalCageAssignment.objects
                .filter(
                    animal=animal,
                    valid_from=HISTORY_START,
                    valid_to=ASSIGNMENT_START,
                )
                .exists()
            )

            if history_exists:
                continue

            AnimalCageAssignment.objects.create(
                animal=animal,
                cage=previous_cage,
                valid_from=HISTORY_START,
                valid_to=ASSIGNMENT_START,
                recorded_by=assigned_by,
                reason=(
                    "Demo historical cage assignment"
                ),
            )
    def get_assigned_by_user(self):
        user = (
            User.objects
            .filter(is_superuser=True)
            .order_by("id")
            .first()
        )

        if user:
            return user

        user = (
            User.objects
            .filter(is_active=True)
            .order_by("id")
            .first()
        )

        if user:
            return user

        raise RuntimeError(
            "Create at least one Django user before running "
            "seed_demo."
        )

    def create_strains(self):
        strain_names = [
            "C57BL/6J",
            "BALB/cJ",
            "129S1/SvImJ",
            "DBA/2J",
        ]

        strains = []

        for name in strain_names:
            strain, _ = Strain.objects.get_or_create(
                name=name
            )

            strains.append(strain)

        return strains

    def create_rooms(self):
        room_specs = [
            {
                "name": "Mouse Room A",
                "building": "Vivarium",
            },
            {
                "name": "Mouse Room B",
                "building": "Vivarium",
            },
        ]

        rooms = {}

        for spec in room_specs:
            room, _ = Room.objects.get_or_create(
                name=spec["name"],
                defaults={
                    "building": spec["building"],
                },
            )

            rooms[spec["name"]] = room

        return rooms

    def create_racks(
        self,
        *,
        rooms,
        assigned_by,
    ):
        rack_specs = [
            ("Rack A", "Mouse Room A"),
            ("Rack B", "Mouse Room A"),
            ("Rack C", "Mouse Room A"),
            ("Rack D", "Mouse Room B"),
            ("Rack E", "Mouse Room B"),
            ("Rack F", "Mouse Room B"),
        ]

        racks = []

        for rack_code, room_name in rack_specs:
            rack, _ = Rack.objects.get_or_create(
                rack_code=rack_code
            )

            has_current_room = (
                RackRoomAssignment.objects.filter(
                    rack=rack,
                    valid_to__isnull=True,
                    system_to__isnull=True,
                ).exists()
            )

            if not has_current_room:
                RackRoomAssignment.objects.create(
                    rack=rack,
                    room=rooms[room_name],
                    valid_from=ASSIGNMENT_START,
                    recorded_by=assigned_by,
                    reason="Demo colony initial location",
                )

            racks.append(rack)

        return racks

    def create_positions(
        self,
        *,
        racks,
    ):
        positions = []

        for rack in racks:
            for position_number in range(
                1,
                21,
            ):
                position_label = (
                    f"{position_number:02d}"
                )

                position, _ = (
                    RackPosition.objects.get_or_create(
                        rack=rack,
                        position_label=position_label,
                    )
                )

                positions.append(position)

        return positions

    def create_responsibility_users(self):
        user_specs = [
            (
                "danielle.marsh",
                "Danielle",
                "Marsh",
            ),
            (
                "haerin.kang",
                "Haerin",
                "Kang",
            ),
            (
                "hanni.pham",
                "Hanni",
                "Pham",
            ),
            (
                "minji.kim",
                "Minji",
                "Kim",
            ),
            (
                "hyein.lee",
                "Hyein",
                "Lee",
            ),
        ]

        users = []

        for (
            username,
            first_name,
            last_name,
        ) in user_specs:
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                },
            )

            changed = False

            if user.first_name != first_name:
                user.first_name = first_name
                changed = True

            if user.last_name != last_name:
                user.last_name = last_name
                changed = True

            if changed:
                user.save(
                    update_fields=[
                        "first_name",
                        "last_name",
                    ]
                )

            users.append(user)

        return users

    def create_cages(
        self,
        *,
        positions,
        assigned_by,
    ):
        cages = []

        for index in range(1, 91):
            cage_code = f"D{index:03d}"

            if index % 9 == 0:
                cage_type = (
                    Cage.CageType.BREEDING
                )
            else:
                cage_type = (
                    Cage.CageType.STANDARD
                )

            cage, _ = Cage.objects.get_or_create(
                cage_code=cage_code,
                defaults={
                    "cage_type": cage_type,
                },
            )

            has_current_location = (
                CageRackPositionAssignment.objects
                .filter(
                    cage=cage,
                    valid_to__isnull=True,
                    system_to__isnull=True,
                )
                .exists()
            )

            if not has_current_location:
                position = positions[
                    index - 1
                ]

                position_occupied = (
                    CageRackPositionAssignment.objects
                    .filter(
                        rack_position=position,
                        valid_to__isnull=True,
                        system_to__isnull=True,
                    )
                    .exists()
                )

                if not position_occupied:
                    (
                        CageRackPositionAssignment
                        .objects
                        .create(
                            cage=cage,
                            rack_position=position,
                            valid_from=ASSIGNMENT_START,
                            recorded_by=assigned_by,
                            reason=(
                                "Demo colony initial location"
                            ),
                        )
                    )

            cages.append(cage)

        return cages

    def create_animals(
        self,
        *,
        cages,
        strains,
        assigned_by,
    ):
        animal_number = 1

        for cage_index, cage in enumerate(
            cages,
            start=1,
        ):
            for animal_in_cage in range(
                1,
                5,
            ):
                animal_uuid = uuid.uuid5(
                    DEMO_NAMESPACE,
                    (
                        f"demo-animal-"
                        f"{animal_number:04d}"
                    ),
                )

                sex = (
                    Animal.Sex.MALE
                    if animal_number % 2 == 0
                    else Animal.Sex.FEMALE
                )

                birth_date = (
                    ASSIGNMENT_START.date()
                    - timedelta(
                        days=60
                        + (
                            animal_number
                            % 240
                        )
                    )
                )

                strain = strains[
                    (
                        cage_index - 1
                    )
                    % len(strains)
                ]

                animal, _ = (
                    Animal.objects.get_or_create(
                        id=animal_uuid,
                        defaults={
                            "sex": sex,
                            "date_of_birth": (
                                birth_date
                            ),
                            "species": (
                                "Mus musculus"
                            ),
                            "strain": strain,
                        },
                    )
                )

                identifier_value = (
                    f"DM{animal_number:04d}"
                )

                (
                    AnimalLocalIdentifier
                    .objects
                    .get_or_create(
                        animal=animal,
                        identifier_type=(
                            AnimalLocalIdentifier
                            .IdentifierType
                            .OTHER
                        ),
                        value=identifier_value,
                        defaults={
                            "assigned_date": (
                                ASSIGNMENT_START
                                .date()
                            ),
                            "notes": (
                                "Demo colony identifier"
                            ),
                        },
                    )
                )

                has_current_cage = (
                    AnimalCageAssignment.objects
                    .filter(
                        animal=animal,
                        valid_to__isnull=True,
                        system_to__isnull=True,
                    )
                    .exists()
                )

                if not has_current_cage:
                    AnimalCageAssignment.objects.create(
                        animal=animal,
                        cage=cage,
                        valid_from=ASSIGNMENT_START,
                        recorded_by=assigned_by,
                        reason=(
                            "Demo colony initial "
                            "assignment"
                        ),
                    )

                animal_number += 1

    def create_responsibilities(
        self,
        *,
        cages,
        users,
        assigned_by,
    ):
        for index, cage in enumerate(
            cages,
            start=1,
        ):
            current_primary = (
                CageResponsibility.objects
                .filter(
                    cage=cage,
                    responsibility_type=(
                        CageResponsibility
                        .ResponsibilityType
                        .PRIMARY
                    ),
                    valid_from__lte=ASSIGNMENT_START,
                    valid_to__isnull=True,
                )
                .exists()
            )

            if not current_primary:
                owner = users[
                    (
                        index - 1
                    )
                    % len(users)
                ]

                CageResponsibility.objects.create(
                    cage=cage,
                    user=owner,
                    responsibility_type=(
                        CageResponsibility
                        .ResponsibilityType
                        .PRIMARY
                    ),
                    valid_from=ASSIGNMENT_START,
                    assigned_by=assigned_by,
                    notes="Demo primary owner",
                )

            # About 1 in 15 cages currently has
            # temporary vacation coverage.
            if index % 15 == 0:
                has_coverage = (
                    CageResponsibility.objects
                    .filter(
                        cage=cage,
                        responsibility_type=(
                            CageResponsibility
                            .ResponsibilityType
                            .COVERAGE
                        ),
                        valid_from__lte=(
                            COVERAGE_START
                        ),
                        valid_to__gt=(
                            COVERAGE_START
                        ),
                    )
                    .exists()
                )

                if not has_coverage:
                    coverage_user = users[
                        index
                        % len(users)
                    ]

                    CageResponsibility.objects.create(
                        cage=cage,
                        user=coverage_user,
                        responsibility_type=(
                            CageResponsibility
                            .ResponsibilityType
                            .COVERAGE
                        ),
                        valid_from=COVERAGE_START,
                        valid_to=COVERAGE_END,
                        assigned_by=assigned_by,
                        notes=(
                            "Vacation coverage"
                        ),
                    )

    def print_summary(self):
        active_animals = (
            Animal.objects.filter(
                retired_at__isnull=True
            ).count()
        )

        active_cages = (
            Cage.objects.filter(
                retired_at__isnull=True
            ).count()
        )

        husbandry_events = (
            HusbandryEvent.objects
            .filter(
                notes__startswith="Demo"
            )
            .count()
        )

        retired_demo_animals = (
            Animal.objects
            .filter(
                retired_reason=(
                    "Death recorded in demo data"
                )
            )
            .count()
        )

        demo_animals = (
            Animal.objects.filter(
                id__in=[
                    uuid.uuid5(
                        DEMO_NAMESPACE,
                        f"demo-animal-{i:04d}",
                    )
                    for i in range(
                        1,
                        361,
                    )
                ]
            ).count()
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Demo colony seeded successfully."
            )
        )

        self.stdout.write(
            f"Demo animals: {demo_animals}"
        )

        self.stdout.write(
            f"Active animals total: {active_animals}"
        )

        self.stdout.write(
            f"Active cages total: {active_cages}"
        )

        self.stdout.write(
            f"Demo husbandry events: "
            f"{husbandry_events}"
        )

        self.stdout.write(
            f"Demo retired animals: "
            f"{retired_demo_animals}"
        )