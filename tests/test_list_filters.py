"""List filters stay private, bounded, and consistent with the learner's day."""

from datetime import date, datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.accounts.models import UserProfile
from apps.goals.models import DailyGoal
from apps.learning.models import StudySession
from apps.vocabulary.models import Vocabulary

User = get_user_model()
UTC = timezone.utc


class ListFilterTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="filters@example.com")
        self.other = User.objects.create_user(email="other-filters@example.com")
        self.profile = UserProfile.objects.create(user=self.user, timezone="Asia/Ho_Chi_Minh")
        self.client.force_authenticate(self.user)
        self.sessions_url = "/api/v1/study-sessions/"
        self.goals_url = "/api/v1/goals/"
        self.vocabulary_url = "/api/v1/vocabulary/"

    def create_session(self, *, user=None, notes="practice", activity="reading", at=None):
        return StudySession.objects.create(
            user=user or self.user,
            activity_type=activity,
            duration_minutes=15,
            notes=notes,
            studied_at=at or datetime(2026, 11, 9, 5, tzinfo=UTC),
        )

    def result_ids(self, response):
        self.assertEqual(response.status_code, 200)
        return {item["id"] for item in response.data["results"]}

    def test_session_search_activity_and_dates_combine_after_ownership_scope(self):
        expected = self.create_session(notes="Exam preparation reading")
        self.create_session(notes="exam preparation", activity="writing")
        self.create_session(notes="other reading notes")
        self.create_session(notes="exam preparation", at=datetime(2026, 11, 8, 5, tzinfo=UTC))
        self.create_session(user=self.other, notes="exam preparation")
        response = self.client.get(
            self.sessions_url,
            {
                "search": "exam",
                "activity_type": "reading",
                "date_from": "2026-11-09",
                "date_to": "2026-11-09",
            },
        )
        self.assertEqual(self.result_ids(response), {str(expected.pk)})

    def test_goal_search_uses_inclusive_dates_and_ownership_scope(self):
        expected = DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 11, 9),
            target_minutes=30,
            notes="Exam practice",
        )
        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 11, 10),
            target_minutes=30,
            notes="Exam practice",
        )
        DailyGoal.objects.create(
            user=self.user,
            target_date=date(2026, 11, 8),
            target_minutes=30,
            notes="Unrelated practice",
        )
        DailyGoal.objects.create(
            user=self.other,
            target_date=date(2026, 11, 9),
            target_minutes=30,
            notes="Exam practice",
        )
        response = self.client.get(
            self.goals_url,
            {"search": "exam", "date_from": "2026-11-08", "date_to": "2026-11-09"},
        )
        self.assertEqual(self.result_ids(response), {str(expected.pk)})

    def test_vocabulary_search_and_both_choices_combine_with_ownership(self):
        expected = Vocabulary.objects.create(
            user=self.user,
            word="travel",
            meaning="go from place to place",
            translation="du lịch",
            example_sentence="I explore the coast.",
            mastery_level="learning",
            part_of_speech="verb",
        )
        Vocabulary.objects.create(
            user=self.user,
            word="explore",
            meaning="discover",
            mastery_level="new",
            part_of_speech="verb",
        )
        Vocabulary.objects.create(
            user=self.other,
            word="explore",
            meaning="discover",
            mastery_level="learning",
            part_of_speech="verb",
        )
        response = self.client.get(
            self.vocabulary_url,
            {"search": "explore", "mastery_level": "learning", "part_of_speech": "verb"},
        )
        self.assertEqual(self.result_ids(response), {str(expected.pk)})

    def test_vocabulary_search_includes_translation_and_notes(self):
        translated = Vocabulary.objects.create(
            user=self.user, word="hello", meaning="greeting", translation="xin chào"
        )
        noted = Vocabulary.objects.create(
            user=self.user, word="wave", meaning="gesture", notes="greeting gesture"
        )
        translated_response = self.client.get(self.vocabulary_url, {"search": "xin"})
        noted_response = self.client.get(self.vocabulary_url, {"search": "gesture"})
        self.assertEqual(self.result_ids(translated_response), {str(translated.pk)})
        self.assertEqual(self.result_ids(noted_response), {str(noted.pk)})

    def test_invalid_choice_values_return_stable_filter_error(self):
        for url, query in (
            (self.sessions_url, {"activity_type": "invalid"}),
            (self.vocabulary_url, {"mastery_level": "invalid"}),
            (self.vocabulary_url, {"part_of_speech": "invalid"}),
        ):
            with self.subTest(url=url, query=query):
                response = self.client.get(url, query)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.data["error"]["code"], "invalid_filter")

    def test_malformed_dates_and_reversed_ranges_are_rejected(self):
        for url in (self.sessions_url, self.goals_url):
            for query, expected_code in (
                ({"date_from": "not-a-date"}, "validation_error"),
                ({"date_to": "2026-02-30"}, "validation_error"),
                (
                    {"date_from": "2026-11-10", "date_to": "2026-11-09"},
                    "invalid_date_range",
                ),
            ):
                with self.subTest(url=url, query=query):
                    response = self.client.get(url, query)
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(response.data["error"]["code"], expected_code)

    def test_datetime_upper_date_cannot_overflow(self):
        response = self.client.get(self.sessions_url, {"date_to": "9999-12-31"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "validation_error")

    def test_datetime_lower_bound_cannot_underflow_during_utc_conversion(self):
        response = self.client.get(self.sessions_url, {"date_from": "0001-01-01"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "validation_error")

    def test_session_day_boundary_uses_profile_timezone(self):
        before = self.create_session(at=datetime(2026, 11, 8, 16, 59, 59, tzinfo=UTC))
        first = self.create_session(at=datetime(2026, 11, 8, 17, tzinfo=UTC))
        last = self.create_session(at=datetime(2026, 11, 9, 16, 59, 59, tzinfo=UTC))
        after = self.create_session(at=datetime(2026, 11, 9, 17, tzinfo=UTC))
        response = self.client.get(
            self.sessions_url, {"date_from": "2026-11-09", "date_to": "2026-11-09"}
        )
        ids = self.result_ids(response)
        self.assertEqual(ids, {str(first.pk), str(last.pk)})
        self.assertNotIn(str(before.pk), ids)
        self.assertNotIn(str(after.pk), ids)

    def test_inclusive_local_day_handles_both_dst_transitions(self):
        self.profile.timezone = "America/New_York"
        self.profile.save(update_fields=["timezone"])
        for day, start, end in (
            (
                "2026-03-08",
                datetime(2026, 3, 8, 5, tzinfo=UTC),
                datetime(2026, 3, 9, 4, tzinfo=UTC),
            ),
            (
                "2026-11-01",
                datetime(2026, 11, 1, 4, tzinfo=UTC),
                datetime(2026, 11, 2, 5, tzinfo=UTC),
            ),
        ):
            with self.subTest(day=day):
                self.create_session(at=start - timedelta(seconds=1))
                first = self.create_session(at=start)
                last = self.create_session(at=end - timedelta(seconds=1))
                self.create_session(at=end)
                response = self.client.get(self.sessions_url, {"date_from": day, "date_to": day})
                self.assertEqual(self.result_ids(response), {str(first.pk), str(last.pk)})

    def test_missing_profile_and_legacy_invalid_timezone_use_system_default(self):
        first = self.create_session(at=datetime(2026, 11, 8, 17, tzinfo=UTC))
        self.create_session(at=datetime(2026, 11, 9, 17, tzinfo=UTC))
        query = {"date_from": "2026-11-09", "date_to": "2026-11-09"}
        self.profile.timezone = "Invalid/StoredZone"
        self.profile.save(update_fields=["timezone"])
        self.assertEqual(
            self.result_ids(self.client.get(self.sessions_url, query)), {str(first.pk)}
        )
        self.profile.delete()
        # Authentication normally fetches a new user instance on each request.
        self.client.force_authenticate(User.objects.get(pk=self.user.pk))
        self.assertEqual(
            self.result_ids(self.client.get(self.sessions_url, query)), {str(first.pk)}
        )

    def test_pagination_caps_page_size_and_page_two_has_no_overlap(self):
        StudySession.objects.bulk_create(
            [
                StudySession(
                    user=self.user,
                    activity_type="reading",
                    duration_minutes=1,
                    studied_at=datetime(2026, 11, 9, tzinfo=UTC) + timedelta(minutes=index),
                )
                for index in range(125)
            ]
        )
        self.create_session(user=self.other)
        first = self.client.get(self.sessions_url, {"page_size": 1000})
        second = self.client.get(self.sessions_url, {"page_size": 1000, "page": 2})
        first_ids, second_ids = self.result_ids(first), self.result_ids(second)
        self.assertEqual(first.data["count"], 125)
        self.assertEqual(second.data["count"], 125)
        self.assertEqual(len(first_ids), 100)
        self.assertEqual(len(second_ids), 25)
        self.assertFalse(first_ids & second_ids)
        self.assertIsNotNone(first.data["next"])
        self.assertIsNone(second.data["next"])
        default_page = self.client.get(self.sessions_url)
        self.assertEqual(len(default_page.data["results"]), 20)
