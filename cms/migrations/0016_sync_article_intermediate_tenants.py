from django.db import migrations


def backfill_intermediate_tenants(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute('''
            UPDATE cms_article_application aa
            JOIN cms_article a ON aa.article_id = a.id
            SET aa.tenant_id = a.tenant_id
            WHERE aa.tenant_id IS NULL AND a.tenant_id IS NOT NULL;
        ''')
        cursor.execute('''
            UPDATE cms_article_category ac
            JOIN cms_article a ON ac.article_id = a.id
            SET ac.tenant_id = a.tenant_id
            WHERE ac.tenant_id IS NULL AND a.tenant_id IS NOT NULL;
        ''')
        cursor.execute('''
            UPDATE cms_article_tag at_tag
            JOIN cms_article a ON at_tag.article_id = a.id
            SET at_tag.tenant_id = a.tenant_id
            WHERE at_tag.tenant_id IS NULL AND a.tenant_id IS NOT NULL;
        ''')
        cursor.execute('''
            UPDATE cms_article_statistics ast
            JOIN cms_article a ON ast.article_id = a.id
            SET ast.tenant_id = a.tenant_id
            WHERE ast.tenant_id IS NULL AND a.tenant_id IS NOT NULL;
        ''')
        cursor.execute('''
            UPDATE cms_article_version av
            JOIN cms_article a ON av.article_id = a.id
            SET av.tenant_id = a.tenant_id
            WHERE av.tenant_id IS NULL AND a.tenant_id IS NOT NULL;
        ''')


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0015_alter_categorytranslation_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(backfill_intermediate_tenants, reverse_code=migrations.RunPython.noop),
    ]
