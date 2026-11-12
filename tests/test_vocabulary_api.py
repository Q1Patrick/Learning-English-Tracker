"""Regression coverage for vocabulary ownership and uniqueness."""

from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import serializers
from rest_framework.test import APITestCase

from apps.vocabulary.models import Vocabulary
from apps.vocabulary.serializers import VocabularySerializer

User = get_user_model()


class VocabularyAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="vocab@example.com")
        self.other = User.objects.create_user(email="other-vocab@example.com")
        self.client.force_authenticate(self.user)
        self.url = "/api/v1/vocabulary/"
        self.item = Vocabulary.objects.create(user=self.user, word="hello", meaning="a greeting")
        self.other_item = Vocabulary.objects.create(
            user=self.other, word="private", meaning="another user's item"
        )

    def test_duplicate_create_returns_field_error(self):
        response = self.client.post(
            self.url, {"word": " hello ", "meaning": "greeting"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "duplicate_record")
        self.assertIn("word", response.data["error"]["details"])
        self.assertEqual(Vocabulary.objects.filter(user=self.user).count(), 1)

    def test_duplicate_update_returns_field_error(self):
        second = Vocabulary.objects.create(user=self.user, word="world", meaning="earth")
        response = self.client.patch(f"{self.url}{second.pk}/", {"word": "hello"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"]["code"], "duplicate_record")
        second.refresh_from_db()
        self.assertEqual(second.word, "world")

    def test_same_word_on_self_update_is_allowed(self):
        response = self.client.patch(
            f"{self.url}{self.item.pk}/",
            {"word": "hello", "meaning": "updated"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertEqual(self.item.meaning, "updated")

    def test_same_word_is_allowed_for_different_users(self):
        response = self.client.post(
            self.url, {"word": "private", "meaning": "my own definition"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Vocabulary.objects.filter(word="private").count(), 2)

    def test_list_excludes_other_users_records(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.item.pk))

    def test_other_users_item_is_not_readable_or_editable(self):
        url = f"{self.url}{self.other_item.pk}/"
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(
            self.client.patch(url, {"meaning": "changed"}, format="json").status_code,
            404,
        )
        self.assertEqual(self.client.delete(url).status_code, 404)
        self.other_item.refresh_from_db()
        self.assertEqual(self.other_item.meaning, "another user's item")

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get(self.url).status_code, 401)


class VocabularyWriteRaceTests(TestCase):
    """Exercise database fallback after validation has become stale."""

    def setUp(self):
        self.user = User.objects.create_user(email="vocab-race@example.com")
        self.context = {"request": SimpleNamespace(user=self.user)}

    def test_duplicate_after_validation_is_translated_and_transaction_survives(self):
        serializer = VocabularySerializer(
            data={"word": "hello", "meaning": "greeting"}, context=self.context
        )
        serializer.is_valid(raise_exception=True)
        Vocabulary.objects.create(user=self.user, word="hello", meaning="first writer")
        with self.assertRaises(serializers.ValidationError) as error:
            serializer.save(user=self.user)
        self.assertEqual(error.exception.get_codes()["word"][0], "duplicate_record")
        self.assertEqual(Vocabulary.objects.filter(user=self.user).count(), 1)

    def test_unrelated_integrity_error_is_not_mislabeled(self):
        serializer = VocabularySerializer(
            data={"word": "hello", "meaning": "greeting"}, context=self.context
        )
        serializer.is_valid(raise_exception=True)
        with patch.object(
            Vocabulary, "save", side_effect=IntegrityError("unrelated database failure")
        ):
            with self.assertRaisesRegex(IntegrityError, "unrelated database failure"):
                serializer.save(user=self.user)
        self.assertEqual(Vocabulary.objects.count(), 0)
