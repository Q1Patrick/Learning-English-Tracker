"""Transactional server-side scoring with repeat-safe submissions."""

import hashlib
import json
from uuid import UUID

from django.db import IntegrityError, transaction
from rest_framework.exceptions import NotFound

from common.database import retry_sqlite_locked
from common.exceptions import APIError

from .models import Choice, Question, Quiz, QuizAttempt, QuizAttemptAnswer


def parse_idempotency_key(value):
    if value is None:
        return None
    try:
        return UUID(value)
    except (TypeError, ValueError, AttributeError) as exc:
        raise APIError("Idempotency-Key must be a UUID.", "invalid_idempotency_key") from exc


def _fingerprint(quiz_id, answers):
    payload = {
        "quiz_id": str(quiz_id),
        "answers": sorted(
            (str(answer["question_id"]), str(answer["choice_id"])) for answer in answers
        ),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _replay(user, key, fingerprint):
    if key is None:
        return None
    attempt = QuizAttempt.objects.filter(user=user, idempotency_key=key).first()
    if attempt is not None and attempt.request_fingerprint != fingerprint:
        raise APIError(
            "This Idempotency-Key was already used for a different submission.",
            "idempotency_conflict",
            status_code=409,
        )
    return attempt


def _score_submission(user, quiz, answers, key, fingerprint):
    # Lock content in a fixed order before deriving both score and snapshots.
    if not quiz.is_active:
        raise NotFound("Quiz not found.")
    questions = list(Question.objects.select_for_update().filter(quiz=quiz).order_by("order", "id"))
    if not questions:
        raise APIError("This quiz has no questions.", "quiz_unavailable", status_code=409)
    if any(q.question_type != Question.QuestionType.MULTIPLE_CHOICE for q in questions):
        raise APIError(
            "This quiz contains a question type that cannot be scored yet.",
            "unsupported_question_type",
            status_code=409,
        )

    answer_map = {answer["question_id"]: answer["choice_id"] for answer in answers}
    expected_ids = {q.pk for q in questions}
    if len(answer_map) != len(answers):
        raise APIError("Each question must be answered once.", "duplicate_answer")
    if set(answer_map) != expected_ids:
        raise APIError(
            "Provide exactly one answer for every question in this quiz.", "invalid_answers"
        )

    choices = list(
        Choice.objects.select_for_update()
        .filter(question_id__in=expected_ids)
        .order_by("question_id", "id")
    )
    choices_by_question = {question_id: [] for question_id in expected_ids}
    for choice in choices:
        choices_by_question[choice.question_id].append(choice)

    snapshots = []
    for question in questions:
        question_choices = choices_by_question[question.pk]
        correct_choices = [choice for choice in question_choices if choice.is_correct]
        if len(question_choices) < 2 or len(correct_choices) != 1:
            raise APIError(
                "This quiz has an invalid set of choices.", "quiz_unavailable", status_code=409
            )
        selected = next(
            (choice for choice in question_choices if choice.pk == answer_map[question.pk]),
            None,
        )
        if selected is None:
            raise APIError("A selected choice does not belong to its question.", "invalid_answers")
        correct = correct_choices[0]
        snapshots.append(
            QuizAttemptAnswer(
                question=question,
                choice=selected,
                question_id_snapshot=question.pk,
                choice_id_snapshot=selected.pk,
                correct_choice_id_snapshot=correct.pk,
                question_text=question.text,
                choice_text=selected.text,
                correct_choice_text=correct.text,
                explanation=question.explanation,
                is_correct=selected.is_correct,
                order=question.order,
            )
        )

    correct_count = sum(answer.is_correct for answer in snapshots)
    # Integer rounding with halves rounded up; score always lies between 0 and 100.
    score = (correct_count * 100 + len(questions) // 2) // len(questions)
    attempt = QuizAttempt.objects.create(
        user=user,
        quiz=quiz,
        quiz_id_snapshot=quiz.pk,
        quiz_title_snapshot=quiz.title,
        score=score,
        correct_answers=correct_count,
        total_questions=len(questions),
        idempotency_key=key,
        request_fingerprint=fingerprint,
    )
    for snapshot in snapshots:
        snapshot.attempt = attempt
    QuizAttemptAnswer.objects.bulk_create(snapshots)
    return attempt


def _submit_quiz_once(user, quiz_id, answers, idempotency_key, fingerprint):
    existing = _replay(user, idempotency_key, fingerprint)
    if existing is not None:
        return existing, False
    try:
        with transaction.atomic():
            quiz = Quiz.objects.select_for_update().filter(pk=quiz_id).first()
            # Repeat after taking the lock: another request may have finished
            # while this request waited for the same quiz.
            existing = _replay(user, idempotency_key, fingerprint)
            if existing is not None:
                return existing, False
            if quiz is None:
                raise NotFound("Quiz not found.")
            attempt = _score_submission(user, quiz, answers, idempotency_key, fingerprint)
            return attempt, True
    except IntegrityError:
        # Rollback precedes the replay query, so the connection remains usable.
        # An unrelated integrity error retains its original traceback.
        existing = _replay(user, idempotency_key, fingerprint)
        if existing is not None:
            return existing, False
        raise


def submit_quiz(*, user, quiz_id, answers, idempotency_key=None):
    """Return (attempt, created); callers may retry with the same UUID key.

    SQLite has no row-level SELECT FOR UPDATE. A bounded retry restarts the
    whole rolled-back transaction when another SQLite writer briefly holds
    its table lock. Other database failures keep their original traceback.
    """
    fingerprint = _fingerprint(quiz_id, answers)
    return retry_sqlite_locked(
        lambda: _submit_quiz_once(user, quiz_id, answers, idempotency_key, fingerprint)
    )
