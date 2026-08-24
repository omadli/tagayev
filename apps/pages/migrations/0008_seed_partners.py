"""Partner seeding removed for this site — partners are added from the admin.

The file (and its migration class) stays because later migrations declare a
dependency on it; only the data step is gone.
"""
from django.db import migrations


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("pages", "0007_partner"),
    ]

    operations = [
        migrations.RunPython(noop, noop),
    ]
