from allauth.account.signals import user_logged_in
from django.dispatch import receiver

from colony.models import UserRole


@receiver(user_logged_in)
def ensure_demo_role(sender, request, user, **kwargs):
    UserRole.objects.get_or_create(
        user=user,
        defaults={
            "role": UserRole.Role.LAB_MANAGER,
        },
    )