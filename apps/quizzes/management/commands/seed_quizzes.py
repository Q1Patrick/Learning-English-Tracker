"""Create versioned sample quizzes once, preserving every existing quiz."""

import logging
import re
from dataclasses import dataclass

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, transaction

from apps.quizzes.models import Choice, Question, Quiz
from apps.quizzes.seed_data import QUIZ_SEEDS, ChoiceSeed, QuestionSeed, QuizSeed, seed_uuid

logger = logging.getLogger(__name__)
LOCAL_SETTINGS = {"config.settings.development", "config.settings.test"}


@dataclass(frozen=True)
class PreparedQuiz:
    quiz: Quiz
    questions: tuple
    choices: tuple


def _require(condition, message):
    if not condition:
        raise CommandError(f"Invalid sample quiz data: {message}")


def _validate_model(instance, *, exclude=()):
    try:
        instance.full_clean(exclude=exclude, validate_unique=False, validate_constraints=False)
    except ValidationError as error:
        fields = ", ".join(sorted(error.message_dict))
        raise CommandError(
            f"Invalid sample quiz data: {instance._meta.object_name} fields ({fields})."
        ) from error


def prepare_seed_data(seeds):
    """Validate all content before any mutation, including rows that may be skipped."""
    _require(isinstance(seeds, tuple) and bool(seeds), "provide a non-empty tuple of quizzes.")
    seen_ids = set()
    prepared = []

    def reserve(identifier):
        _require(identifier not in seen_ids, "duplicate content identifiers.")
        seen_ids.add(identifier)
        return identifier

    def validate_slug(value):
        _require(
            isinstance(value, str) and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value),
            "slugs must contain lowercase words separated by hyphens.",
        )

    for seed in seeds:
        _require(isinstance(seed, QuizSeed), "each quiz must be a QuizSeed.")
        validate_slug(seed.slug)
        _require(
            type(seed.version) is int and seed.version > 0, "versions must be positive integers."
        )
        _require(
            isinstance(seed.questions, tuple) and len(seed.questions) >= 3,
            "each quiz needs at least three questions.",
        )
        _require(
            isinstance(seed.title, str) and bool(seed.title.strip()), "quiz titles are required."
        )
        _require(
            isinstance(seed.description, str) and bool(seed.description.strip()),
            "quiz descriptions are required.",
        )
        quiz = Quiz(
            id=reserve(seed_uuid(seed, "quiz")),
            title=seed.title,
            description=seed.description,
            difficulty=seed.difficulty,
            is_active=True,
        )
        _validate_model(quiz)
        questions, choices = [], []
        for question_order, question_seed in enumerate(seed.questions, start=1):
            _require(
                isinstance(question_seed, QuestionSeed), "each question must be a QuestionSeed."
            )
            validate_slug(question_seed.slug)
            _require(
                isinstance(question_seed.text, str) and bool(question_seed.text.strip()),
                "question text is required.",
            )
            _require(
                isinstance(question_seed.explanation, str)
                and bool(question_seed.explanation.strip()),
                "question explanations are required.",
            )
            _require(
                isinstance(question_seed.choices, tuple) and len(question_seed.choices) == 4,
                "each question needs exactly four choices.",
            )
            _require(
                all(isinstance(choice, ChoiceSeed) for choice in question_seed.choices),
                "each choice must be a ChoiceSeed.",
            )
            _require(
                all(type(choice.is_correct) is bool for choice in question_seed.choices),
                "correct-answer flags must be booleans.",
            )
            _require(
                sum(choice.is_correct for choice in question_seed.choices) == 1,
                "each question must have exactly one correct choice.",
            )
            question = Question(
                id=reserve(seed_uuid(seed, "question", question_seed.slug)),
                quiz_id=quiz.pk,
                text=question_seed.text,
                explanation=question_seed.explanation,
                question_type=Question.QuestionType.MULTIPLE_CHOICE,
                order=question_order,
            )
            _validate_model(question, exclude=("quiz",))
            questions.append(question)
            choice_texts = set()
            for choice_order, choice_seed in enumerate(question_seed.choices, start=1):
                _require(
                    isinstance(choice_seed.text, str) and bool(choice_seed.text.strip()),
                    "choice text is required.",
                )
                normalized = choice_seed.text.strip().casefold()
                _require(normalized not in choice_texts, "choices in a question must be distinct.")
                choice_texts.add(normalized)
                choice = Choice(
                    id=reserve(seed_uuid(seed, "choice", question_seed.slug, str(choice_order))),
                    question_id=question.pk,
                    text=choice_seed.text,
                    is_correct=choice_seed.is_correct,
                    order=choice_order,
                )
                _validate_model(choice, exclude=("question",))
                choices.append(choice)
        prepared.append(PreparedQuiz(quiz, tuple(questions), tuple(choices)))
    return tuple(prepared)


class Command(BaseCommand):
    help = (
        "Create five sample English quizzes. Existing seed IDs are skipped in full; "
        "manual content, inactive flags and history are preserved."
    )
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Validate and report counts without writes."
        )
        parser.add_argument(
            "--allow-production",
            action="store_true",
            help="Explicitly allow seeding with production or custom settings.",
        )

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE not in LOCAL_SETTINGS and not options["allow_production"]:
            raise CommandError(
                "Sample seeding is limited to development/test settings. "
                "Use --allow-production explicitly for production or custom settings."
            )
        prepared = prepare_seed_data(QUIZ_SEEDS)
        if options["dry_run"]:
            existing_ids = set(
                Quiz.objects.filter(pk__in=[item.quiz.pk for item in prepared]).values_list(
                    "pk", flat=True
                )
            )
            self.stdout.write(
                f"Dry run: would create {len(prepared) - len(existing_ids)} quiz(es); "
                f"would skip {len(existing_ids)} existing quiz(es). Database unchanged."
            )
            return

        created = skipped = 0
        try:
            with transaction.atomic():
                for item in prepared:
                    _, is_new = Quiz.objects.get_or_create(
                        pk=item.quiz.pk,
                        defaults={
                            "title": item.quiz.title,
                            "description": item.quiz.description,
                            "difficulty": item.quiz.difficulty,
                            "is_active": True,
                        },
                    )
                    if not is_new:
                        skipped += 1
                        continue
                    Question.objects.bulk_create(item.questions)
                    Choice.objects.bulk_create(item.choices)
                    created += 1
        except DatabaseError as error:
            logger.exception("Sample quiz creation failed; seed transaction rolled back.")
            raise CommandError("Quiz seeding failed; no new sample quizzes were saved.") from error
        self.stdout.write(
            self.style.SUCCESS(f"Created {created} quiz(es); skipped {skipped} existing quiz(es).")
        )
