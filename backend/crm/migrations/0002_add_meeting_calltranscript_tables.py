from django.db import migrations


def create_missing_tables(apps, schema_editor):
    CallTranscript = apps.get_model("crm", "CallTranscript")
    Meeting = apps.get_model("crm", "Meeting")

    existing_tables = schema_editor.connection.introspection.table_names()

    if CallTranscript._meta.db_table not in existing_tables:
        schema_editor.create_model(CallTranscript)

    # Refresh because the previous CREATE TABLE changed the database
    existing_tables = schema_editor.connection.introspection.table_names()

    if Meeting._meta.db_table not in existing_tables:
        schema_editor.create_model(Meeting)


def reverse_noop(apps, schema_editor):
    # Do not automatically delete these tables during rollback,
    # because this is a database repair migration.
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ("crm", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_missing_tables,
            reverse_noop,
        ),
    ]