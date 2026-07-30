from django.db import transaction
from django.utils import timezone

from we_rss.models import MemberArticleState


class MemberArticleStateService:
    @staticmethod
    def _cleanup_empty_state(state):
        if state.is_hidden or state.is_favorite:
            return state
        state.delete()
        return None

    @staticmethod
    def set_hidden(*, article, member, is_hidden):
        now = timezone.now()
        state, _created = MemberArticleState.objects.get_or_create(
            tenant=article.tenant,
            member=member,
            article=article,
            defaults={
                "is_hidden": is_hidden,
                "hidden_at": now if is_hidden else None,
            },
        )
        if state.is_hidden != is_hidden:
            state.is_hidden = is_hidden
            state.hidden_at = now if is_hidden else None
            state.save(update_fields=["is_hidden", "hidden_at", "updated_at"])
        return MemberArticleStateService._cleanup_empty_state(state)

    @staticmethod
    def set_favorite(*, article, member, is_favorite):
        now = timezone.now()
        state, _created = MemberArticleState.objects.get_or_create(
            tenant=article.tenant,
            member=member,
            article=article,
            defaults={
                "is_favorite": is_favorite,
                "favorited_at": now if is_favorite else None,
            },
        )
        if state.is_favorite != is_favorite:
            state.is_favorite = is_favorite
            state.favorited_at = now if is_favorite else None
            state.save(update_fields=["is_favorite", "favorited_at", "updated_at"])
        return MemberArticleStateService._cleanup_empty_state(state)

    @staticmethod
    def bulk_hide_articles(*, tenant, member, article_ids):
        if not article_ids:
            return

        now = timezone.now()
        existing_states = {
            state.article_id: state
            for state in MemberArticleState.objects.filter(
                tenant=tenant,
                member=member,
                article_id__in=article_ids,
            )
        }
        states_to_create = []
        states_to_update = []

        for article_id in article_ids:
            state = existing_states.get(article_id)
            if state is None:
                states_to_create.append(
                    MemberArticleState(
                        tenant=tenant,
                        member=member,
                        article_id=article_id,
                        is_hidden=True,
                        hidden_at=now,
                    )
                )
                continue
            if state.is_hidden:
                continue
            state.is_hidden = True
            state.hidden_at = now
            state.updated_at = now
            states_to_update.append(state)

        with transaction.atomic():
            if states_to_create:
                MemberArticleState.objects.bulk_create(states_to_create)
            if states_to_update:
                MemberArticleState.objects.bulk_update(
                    states_to_update,
                    ["is_hidden", "hidden_at", "updated_at"],
                )
