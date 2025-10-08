# Generated manually for product-plan consistency check

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0001_initial'),
    ]

    operations = [
        # 添加CHECK约束确保product和plan的一致性
        migrations.RunSQL(
            sql="""
                ALTER TABLE licenses_license 
                ADD CONSTRAINT check_product_plan_consistency 
                CHECK (
                    product_id = (
                        SELECT product_id 
                        FROM licenses_license_plan 
                        WHERE id = plan_id
                    )
                );
            """,
            reverse_sql="""
                ALTER TABLE licenses_license 
                DROP CONSTRAINT check_product_plan_consistency;
            """,
        ),
        
        # 添加触发器自动同步product
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION sync_license_product()
                RETURNS TRIGGER AS $$
                BEGIN
                    -- 如果plan改变了，自动更新product
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
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS trigger_sync_license_product ON licenses_license;
                DROP FUNCTION IF EXISTS sync_license_product();
            """,
        ),
    ]
