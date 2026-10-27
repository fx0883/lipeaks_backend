# Generated manually for product-plan consistency check

from django.db import migrations


def apply_pg_triggers(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            ALTER TABLE licenses_license 
            ADD CONSTRAINT check_product_plan_consistency 
            CHECK (
                product_id = (
                    SELECT product_id 
                    FROM licenses_license_plan 
                    WHERE id = plan_id
                )
            );
        """)
        schema_editor.execute("""
            CREATE OR REPLACE FUNCTION sync_license_product()
            RETURNS TRIGGER AS $$
            BEGIN
                IF NEW.plan_id IS NOT NULL THEN
                    NEW.product_id := (
                        SELECT product_id 
                        FROM licenses_license_plan 
                        WHERE id = NEW.plan_id
                    );
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER trigger_sync_license_product
                BEFORE INSERT OR UPDATE ON licenses_license
                FOR EACH ROW
                EXECUTE FUNCTION sync_license_product();
        """)


def revert_pg_triggers(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute("""
            DROP TRIGGER IF EXISTS trigger_sync_license_product ON licenses_license;
            DROP FUNCTION IF EXISTS sync_license_product();
            ALTER TABLE licenses_license 
            DROP CONSTRAINT IF EXISTS check_product_plan_consistency;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(apply_pg_triggers, revert_pg_triggers),
    ]
