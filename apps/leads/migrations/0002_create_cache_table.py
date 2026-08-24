"""Create the DatabaseCache table used by the lead-form rate limiter.

settings.CACHES uses ``django.core.cache.backends.db.DatabaseCache`` (table
``tagayev_cache``), which Django does NOT create via the model migrations —
it normally needs a one-off ``manage.py createcachetable`` at deploy. Forgetting
that step makes every POST /ariza/ raise ``no such table: tagayev_cache``.

Folding it into a migration makes the table part of the standard ``migrate``
flow, so a fresh install or a reset DB can never miss it again. Idempotent:
``createcachetable`` skips a table that already exists.
"""
from django.core.management import call_command
from django.db import migrations


def create_cache_table(apps, schema_editor):
    call_command("createcachetable", verbosity=0)


class Migration(migrations.Migration):
    # createcachetable issues its own DDL/commit; keep it outside the migration
    # transaction (and SQLite is happiest with DDL run this way).
    atomic = False

    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        # Reverse is a no-op: never drop the shared cache table on rollback.
        migrations.RunPython(create_cache_table, migrations.RunPython.noop),
    ]
