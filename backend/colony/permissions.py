from rest_framework.permissions import BasePermission, SAFE_METHODS

from colony.models import UserRole

"""
Colony authorization matrix
============================

Role                    Move Animals/Cages    Record Husbandry    Undo Operations
---------------------------------------------------------------------------------
Principal Investigator        Yes                  Yes                  Yes
Lab Manager                   Yes                  Yes                  Yes
Researcher                    Yes                  Yes                   No
Student                        No                  Yes                   No
Facility Veterinarian          No                  Yes                   No

Permission rationale:
- PI and Lab Manager have full operational control of the colony.
- Researchers can perform routine colony operations and record husbandry events,
  but cannot undo audited operations.
- Students can record husbandry events but cannot change animal/cage locations
  or undo operations.
- Facility Veterinarians can record health/husbandry information but cannot
  change general colony locations or undo operations.
- Undo is restricted to PI and Lab Manager because it creates a compensating
  operation that changes current colony state.

UserRole also supports optional room-scoped roles through scope_room. Room-level
permission enforcement is represented in the data model but is not currently
enforced by these API permission classes.
"""


class HasColonyRole(BasePermission):
    """
    Require an authenticated user with at least one colony role
    for write operations.

    Read-only requests remain allowed.
    """

    message = "You do not have permission to modify colony data."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        return UserRole.objects.filter(
            user=request.user,
        ).exists()

def user_has_role(user, allowed_roles):
    if not user or not user.is_authenticated:
        return False

    return UserRole.objects.filter(
        user=user,
        role__in=allowed_roles,
    ).exists()


class CanManageColony(BasePermission):
    message = "You do not have permission to manage colony locations."

    def has_permission(self, request, view):
        return user_has_role(
            request.user,
            [
                UserRole.Role.PI,
                UserRole.Role.LAB_MANAGER,
                UserRole.Role.RESEARCHER,
            ],
        )


class CanRecordHusbandry(BasePermission):
    message = "You do not have permission to record husbandry events."

    def has_permission(self, request, view):
        return user_has_role(
            request.user,
            [
                UserRole.Role.PI,
                UserRole.Role.LAB_MANAGER,
                UserRole.Role.RESEARCHER,
                UserRole.Role.STUDENT,
                UserRole.Role.VETERINARIAN,
            ],
        )


class CanUndoOperations(BasePermission):
    message = "You do not have permission to undo operations."

    def has_permission(self, request, view):
        return user_has_role(
            request.user,
            [
                UserRole.Role.PI,
                UserRole.Role.LAB_MANAGER,
            ],
        )