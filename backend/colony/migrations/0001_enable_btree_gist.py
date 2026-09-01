from django.contrib.postgres.operations import BtreeGistExtension
from django.db import migrations


class Migration(migrations.Migration):
    """Must run before any migration that creates AnimalCageAssignment or
    CageRackPositionAssignment — their ExclusionConstraints need btree_gist
    to already exist. Run `python manage.py makemigrations colony` after
    this one to generate the normal CreateModel migration (call it
    0002_initial); Django will pick up all the models, indexes, and
    constraints from models.py automatically.
    """

    initial = True

    dependencies = []

    operations = [
        BtreeGistExtension(),
    ]
