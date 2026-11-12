from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.ai_feedback.models import AIFeedback


class Command(BaseCommand):
    help = "Mark abandoned pending AI feedback as failed, without calling the provider."

    def add_arguments(self, parser):
        parser.add_argument("--older-than-minutes", type=int, default=60)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        minutes = options["older_than_minutes"]
        request_budget = (
            settings.OPENAI_TIMEOUT_SECONDS * (settings.OPENAI_MAX_RETRIES + 1)
            # The SDK may honor a provider retry-after delay up to 60 seconds.
            + settings.OPENAI_MAX_RETRIES * 60
        )
        if minutes < 10 or minutes * 60 <= request_budget * 2:
            raise CommandError(
                "Choose at least 10 minutes and more than twice the configured "
                "AI timeout/retry budget to avoid expiring active requests."
            )
        now = timezone.now()
        pending = AIFeedback.objects.filter(
            status=AIFeedback.Status.PENDING,
            updated_at__lt=now - timedelta(minutes=minutes),
        )
        if options["dry_run"]:
            self.stdout.write(f"Would expire {pending.count()} pending feedback request(s).")
            return
        count = pending.update(
            status=AIFeedback.Status.FAILED,
            error_code="ai_request_expired",
            error_message="This request was interrupted before feedback was saved.",
            updated_at=now,
        )
        self.stdout.write(self.style.SUCCESS(f"Expired {count} feedback request(s)."))
