import uuid
from datetime import date, datetime, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
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
    Room,
    Strain,
    RackRoomAssignment,
)


class Command(BaseCommand):
    help = "Seed the database with demo colony data."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        admin_user = User.objects.filter(
            is_superuser=True
        ).first()

        if not admin_user:
            raise CommandError(
                "Create a superuser before running the demo seed."
            )

        user = User.objects.filter(is_superuser=True).first()

        if not user:
            raise CommandError(
                "No superuser found. Create one first with "
                "'python manage.py createsuperuser'."
            )

        dani, _ = User.objects.get_or_create(
            username="mo.dani",
            defaults={
                "first_name": "Danielle",
                "last_name": "Marsh",
                "email": "dani@example.com",
            },
        )

        haerin, _ = User.objects.get_or_create(
            username="kang.haerin",
            defaults={
                "first_name": "Haerin",
                "last_name": "Kang",
                "email": "haerin@example.com",
            },
        )

        minji, _ = User.objects.get_or_create(
            username="kim.minji",
            defaults={
                "first_name": "Minji",
                "last_name": "Kim",
                "email": "minji@example.com",
            },
        )

        hanni, _ = User.objects.get_or_create(
            username="pham.hanni",
            defaults={
                "first_name": "Hanni",
                "last_name": "Pham",
                "email": "hanni@example.com",
            },
        )

        hyein, _ = User.objects.get_or_create(
            username="lee.hyein",
            defaults={
                "first_name": "Hyein",
                "last_name": "Lee",
                "email": "hyein@example.com",
            },
        )
        responsibility_start = datetime(
            2026,
            8,
            25,
            8,
            0,
            tzinfo=timezone.utc,
        )

        coverage_start = datetime(
            2026,
            9,
            1,
            7,
            0,
            tzinfo=timezone.utc,
        )

        coverage_end = datetime(
            2026,
            9,
            8,
            7,
            0,
            tzinfo=timezone.utc,
        )

        self.stdout.write("Creating demo colony data...")

        # ---------------------------------------------------------
        # Strains
        # ---------------------------------------------------------

        c57, _ = Strain.objects.get_or_create(
            name="C57BL/6J",
        )

        balb, _ = Strain.objects.get_or_create(
            name="BALB/cJ",
        )

        # ---------------------------------------------------------
        # Rooms
        # ---------------------------------------------------------
        
        # Use a fixed timestamp so rerunning the seed command
        # doesn't create a different temporal assignment.
        assignment_start = datetime(
            2026,
            8,
            25,
            8,
            0,
            tzinfo=timezone.utc,
        )

        room_a, _ = Room.objects.get_or_create(
            name="Mouse Room A",
            defaults={
                "building": "Vivarium",
            },
        )

        room_b, _ = Room.objects.get_or_create(
            name="Mouse Room B",
            defaults={
                "building": "Vivarium",
            },
        )

        # ---------------------------------------------------------
        # Racks
        # ---------------------------------------------------------

        rack_a, _ = Rack.objects.get_or_create(
            rack_code="RACK-A",
            defaults={
                "room": room_a,
            },
        )

        rack_b, _ = Rack.objects.get_or_create(
            rack_code="RACK-B",
            defaults={
                "room": room_b,
            },
        )

        # ---------------------------------------------------------
        # Rack Room Assignment
        # ---------------------------------------------------------

        RackRoomAssignment.objects.get_or_create(
            rack=rack_a,
            room=room_a,
            valid_from=assignment_start,
            defaults={
                "recorded_by": admin_user,
                "reason": "Initial demo rack room assignment",
            },
        )

        RackRoomAssignment.objects.get_or_create(
            rack=rack_b,
            room=room_b,
            valid_from=assignment_start,
            defaults={
                "recorded_by": admin_user,
                "reason": "Initial demo rack room assignment",
            },
        )

        # ---------------------------------------------------------
        # Rack positions
        # ---------------------------------------------------------

        rack_a_positions = []
        rack_b_positions = []

        for number in range(1, 11):
            position_a, _ = RackPosition.objects.get_or_create(
                rack=rack_a,
                position_label=f"A-{number:02d}",
            )

            rack_a_positions.append(position_a)

            position_b, _ = RackPosition.objects.get_or_create(
                rack=rack_b,
                position_label=f"B-{number:02d}",
            )

            rack_b_positions.append(position_b)

        # ---------------------------------------------------------
        # Cages
        # ---------------------------------------------------------

        cages = []

        for number in range(1, 7):
            cage, _ = Cage.objects.get_or_create(
                cage_code=f"CAGE-{number:03d}",
                defaults={
                    "cage_type": (
                        "breeding"
                        if number == 5
                        else "standard"
                    ),
                },
            )

            cages.append(cage)

        primary_assignments = [
            (cages[0], dani),
            (cages[1], haerin),
            (cages[2], hanni),
            (cages[3], minji),
            (cages[4], hyein),
            (cages[5], dani),
        ]

        for cage, user in primary_assignments:
            CageResponsibility.objects.get_or_create(
                cage=cage,
                user=user,
                responsibility_type=CageResponsibility.ResponsibilityType.PRIMARY,
                valid_from=responsibility_start,
                defaults={
                    "assigned_by": admin_user,
                    "notes": "Demo primary cage responsibility",
                },
            )

        CageResponsibility.objects.get_or_create(
            cage=cages[0],
            user=haerin,
            responsibility_type=CageResponsibility.ResponsibilityType.COVERAGE,
            valid_from=coverage_start,
            valid_to=coverage_end,
            defaults={
                "assigned_by": admin_user,
                "notes": "Demo temporary vacation coverage",
            },
        )

        

        # ---------------------------------------------------------
        # Cage -> rack position assignments
        # ---------------------------------------------------------

        for cage, rack_position in zip(
            cages,
            rack_a_positions[:6],
        ):
            CageRackPositionAssignment.objects.get_or_create(
                cage=cage,
                rack_position=rack_position,
                valid_from=assignment_start,
                defaults={
                    "recorded_by": user,
                },
            )

        # ---------------------------------------------------------
        # Animals
        # ---------------------------------------------------------

        animals = []

        for number in range(1, 13):
            # Deterministic UUID means rerunning the seed command
            # refers to the same demo animal.
            animal_id = uuid.uuid5(
                uuid.NAMESPACE_DNS,
                f"salk-colony-demo-animal-{number}",
            )

            animal, _ = Animal.objects.get_or_create(
                id=animal_id,
                defaults={
                    "sex": (
                        Animal.Sex.FEMALE
                        if number % 2 == 0
                        else Animal.Sex.MALE
                    ),
                    "date_of_birth": date(
                        2026,
                        6,
                        1 + (number % 10),
                    ),
                    "species": "Mus musculus",
                    "strain": (
                        c57
                        if number <= 8
                        else balb
                    ),
                },
            )

            animals.append(animal)

            # Human-readable identifier for the UI.
            AnimalLocalIdentifier.objects.get_or_create(
                animal=animal,
                identifier_type=(
                    AnimalLocalIdentifier.IdentifierType.EAR_TAG
                ),
                value=f"M{number:03d}",
                defaults={
                    "assigned_date": date(2026, 6, 15),
                    "notes": "Demo ear tag",
                },
            )

        # ---------------------------------------------------------
        # Animal -> cage assignments
        # ---------------------------------------------------------

        # Two animals per cage:
        #
        # CAGE-001 -> M001, M002
        # CAGE-002 -> M003, M004
        # CAGE-003 -> M005, M006
        # CAGE-004 -> M007, M008
        # CAGE-005 -> M009, M010
        # CAGE-006 -> M011, M012

        for index, animal in enumerate(animals):
            cage_index = index // 2
            cage = cages[cage_index]

            AnimalCageAssignment.objects.get_or_create(
                animal=animal,
                cage=cage,
                valid_from=assignment_start,
                defaults={
                    "recorded_by": user,
                },
            )

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        self.stdout.write(
            self.style.SUCCESS(
                "Demo colony data created successfully."
            )
        )

        self.stdout.write(
            f"Rooms: {Room.objects.count()}"
        )

        self.stdout.write(
            f"Racks: {Rack.objects.count()}"
        )

        self.stdout.write(
            f"Rack positions: {RackPosition.objects.count()}"
        )

        self.stdout.write(
            f"Cages: {Cage.objects.count()}"
        )

        self.stdout.write(
            f"Animals: {Animal.objects.count()}"
        )

        self.stdout.write(
            "Animal identifiers: "
            f"{AnimalLocalIdentifier.objects.count()}"
        )

        self.stdout.write(
            "Animal-cage assignments: "
            f"{AnimalCageAssignment.objects.count()}"
        )

        self.stdout.write(
            "Cage-position assignments: "
            f"{CageRackPositionAssignment.objects.count()}"
        )