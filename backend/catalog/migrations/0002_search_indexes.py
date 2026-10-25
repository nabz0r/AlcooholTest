from django.db import migrations

def forwards(apps,schema_editor):
    if schema_editor.connection.vendor!='postgresql': return
    with schema_editor.connection.cursor() as cur:
        cur.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
        for table,name in [('catalog_product','product'),('catalog_brand','brand'),('catalog_ingredient','ingredient')]:
            cur.execute(f'CREATE INDEX {name}_name_trgm ON {table} USING gin (UPPER(name) gin_trgm_ops)')

def backwards(apps,schema_editor):
    if schema_editor.connection.vendor!='postgresql': return
    with schema_editor.connection.cursor() as cur:
        for name in ['product','brand','ingredient']: cur.execute(f'DROP INDEX IF EXISTS {name}_name_trgm')
class Migration(migrations.Migration):
    dependencies=[('catalog','0001_initial')]
    operations=[migrations.RunPython(forwards,backwards)]
