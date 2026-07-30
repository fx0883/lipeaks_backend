from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("we_rss", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="wechatarticle",
            name="article_type",
            field=models.CharField(
                choices=[("news", "News"), ("newspic", "Newspic")],
                default="news",
                max_length=20,
            ),
        ),
    ]
