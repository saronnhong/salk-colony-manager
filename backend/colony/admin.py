from django.contrib import admin

from .models import (
    Animal,
    AnimalCageAssignment,
    Cage,
    CageRackPositionAssignment,
    Rack,
    RackPosition,
    Room,
    Strain,
    AnimalLocalIdentifier,
    RackCurrentRoom
)
from .models import CageResponsibility

admin.site.register(CageResponsibility)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("name", "building", "retired_at")
    search_fields = ("name", "building")


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ("rack_code", "current_room_name")

    def current_room_name(self, obj):
        try:
            return obj.current_room.room.name
        except RackCurrentRoom.DoesNotExist:
            return "—"

    current_room_name.short_description = "Current room"


@admin.register(RackPosition)
class RackPositionAdmin(admin.ModelAdmin):
    list_display = (
        "position_label",
        "rack",
    )
    search_fields = (
        "position_label",
        "rack__rack_code",
        "rack__room__name",
    )


@admin.register(Strain)
class StrainAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Cage)
class CageAdmin(admin.ModelAdmin):
    list_display = (
        "cage_code",
        "cage_type",
        "retired_at",
        "created_at",
    )
    list_filter = ("cage_type",)
    search_fields = ("cage_code",)


@admin.register(Animal)
class AnimalAdmin(admin.ModelAdmin):
    # list_display = (
    #     "id",
    #     "sex",
    #     "date_of_birth",
    #     "species",
    #     "strain",
    #     "retired_at",
    # )
    @admin.display(description="Identifier")
    def primary_identifier(self, obj):
        identifier = (
            obj.local_identifiers
            .filter(retired_date__isnull=True)
            .order_by("assigned_date")
            .first()
        )
    
        return identifier.value if identifier else "—"
    
    list_display = (
        "primary_identifier",
        "sex",
        "date_of_birth",
        "species",
        "strain",
        "retired_at",
    )
    list_filter = ("sex", "species", "strain")
    search_fields = ("id", "local_identifiers__value",)


@admin.register(AnimalCageAssignment)
class AnimalCageAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "animal",
        "cage",
        "valid_from",
        "valid_to",
        "recorded_by",
    )
    list_filter = ("cage",)
    search_fields = ("animal__id", "cage__cage_code")
    readonly_fields = ("system_from",)


@admin.register(CageRackPositionAssignment)
class CageRackPositionAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "cage",
        "rack_position",
        "valid_from",
        "valid_to",
        "recorded_by",
    )
    search_fields = (
        "cage__cage_code",
        "rack_position__position_label",
        "rack_position__rack__rack_code",
    )
    readonly_fields = ("system_from",)

@admin.register(AnimalLocalIdentifier)
class AnimalLocalIdentifierAdmin(admin.ModelAdmin):
    list_display = (
        "value",
        "identifier_type",
        "animal",
        "assigned_date",
        "retired_date",
    )

    list_filter = (
        "identifier_type",
        "retired_date",
    )

    search_fields = (
        "value",
        "animal__id",
    )