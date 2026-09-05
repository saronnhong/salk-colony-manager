from django.apps import AppConfig


class ColonyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "colony"

    def ready(self):
        import colony.signals  # noqa: F401
