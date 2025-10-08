# Generated manually for RIPER-5 schema refactoring
# Renames LicensePlan fields to clarify template vs instance semantics

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licenses', '0003_licenseassignment'),
    ]

    operations = [
        # 重命名 max_machines -> default_max_activations
        migrations.RenameField(
            model_name='licenseplan',
            old_name='max_machines',
            new_name='default_max_activations',
        ),
        # 重命名 validity_days -> default_validity_days
        migrations.RenameField(
            model_name='licenseplan',
            old_name='validity_days',
            new_name='default_validity_days',
        ),
    ]
