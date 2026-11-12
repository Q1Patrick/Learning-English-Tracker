import json

from django.core.management.base import BaseCommand, CommandError

from apps.accounts.models import UserProfile
from apps.ai_feedback.services import generate_ai_feedback
from common.exceptions import APIError


class Command(BaseCommand):
    help = (
        "Make one real AI feedback request using configured credentials. "
        "This incurs provider usage; it does not create a database record."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--text", default="I go to school yesterday.", help="A sample English sentence."
        )
        parser.add_argument(
            "--english-level", choices=UserProfile.EnglishLevel.values, default="A1"
        )

    def handle(self, *args, **options):
        text = options["text"].strip()
        if not 3 <= len(text) <= 5000:
            raise CommandError("Text must contain between 3 and 5000 characters.")
        try:
            feedback = generate_ai_feedback(text, english_level=options["english_level"])
        except APIError as exc:
            raise CommandError(f"{exc.get_codes()}: {exc.detail}") from None
        self.stdout.write(json.dumps(feedback, ensure_ascii=False, indent=2))
