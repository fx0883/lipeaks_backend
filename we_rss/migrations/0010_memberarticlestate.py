from django.db import migrations, models


def migrate_member_article_favorites_to_state(apps, schema_editor):
    MemberArticleFavorite = apps.get_model("we_rss", "MemberArticleFavorite")
    MemberArticleState = apps.get_model("we_rss", "MemberArticleState")

    states_to_create = []
    for favorite in MemberArticleFavorite.objects.all().iterator():
        states_to_create.append(
            MemberArticleState(
                tenant_id=favorite.tenant_id,
                member_id=favorite.member_id,
                article_id=favorite.article_id,
                is_hidden=False,
                is_favorite=True,
                hidden_at=None,
                favorited_at=favorite.created_at,
                created_at=favorite.created_at,
                updated_at=favorite.created_at,
            )
        )

    if states_to_create:
        MemberArticleState.objects.bulk_create(states_to_create, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("we_rss", "0009_add_feed_content_refresh_task_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="MemberArticleState",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("is_hidden", models.BooleanField(default=False)),
                ("is_favorite", models.BooleanField(default=False)),
                ("hidden_at", models.DateTimeField(blank=True, null=True)),
                ("favorited_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "article",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="member_states",
                        to="we_rss.wechatarticle",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="we_rss_article_states",
                        to="users.member",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="we_rss_member_article_states",
                        to="tenants.tenant",
                    ),
                ),
            ],
            options={
                "db_table": "we_rss_member_article_state",
                "ordering": ["-updated_at", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="memberarticlestate",
            constraint=models.UniqueConstraint(
                fields=("member", "article"),
                name="we_rss_member_article_state_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="memberarticlestate",
            index=models.Index(fields=["tenant", "member", "article"], name="we_rss_memb_tenant__4fec03_idx"),
        ),
        migrations.AddIndex(
            model_name="memberarticlestate",
            index=models.Index(
                fields=["tenant", "member", "is_hidden", "article"],
                name="we_rss_memb_tenant__dcc0f8_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="memberarticlestate",
            index=models.Index(
                fields=["tenant", "member", "is_favorite", "article"],
                name="we_rss_memb_tenant__8b8fb9_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="memberarticlestate",
            index=models.Index(fields=["tenant", "article"], name="we_rss_memb_tenant__4233d4_idx"),
        ),
        migrations.RunPython(migrate_member_article_favorites_to_state, migrations.RunPython.noop),
    ]
