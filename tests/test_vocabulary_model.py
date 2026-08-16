from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.vocabulary.models import Vocabulary


User = get_user_model()


class VocabularyModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.com",
            password="StrongPassword123!",
        )

    def test_create_vocabulary(self):
        vocabulary = Vocabulary.objects.create(
            user=self.user,
            word="figure out",
            meaning="to understand something",
            part_of_speech=Vocabulary.PartOfSpeech.PHRASAL_VERB,
        )

        self.assertEqual(
            vocabulary.user,
            self.user,
        )

        self.assertEqual(
            vocabulary.word,
            "figure out",
        )

        self.assertEqual(
            vocabulary.mastery_level,
            Vocabulary.MasteryLevel.NEW,
        )

    def test_user_cannot_save_duplicate_word(self):
        Vocabulary.objects.create(
            user=self.user,
            word="appointment",
            meaning="a scheduled meeting",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Vocabulary.objects.create(
                    user=self.user,
                    word="appointment",
                    meaning="meeting",
                )

    def test_different_users_can_save_same_word(self):
        other_user = User.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
        )

        Vocabulary.objects.create(
            user=self.user,
            word="maintain",
            meaning="to keep something in good condition",
        )

        Vocabulary.objects.create(
            user=other_user,
            word="maintain",
            meaning="to continue something",
        )

        self.assertEqual(
            Vocabulary.objects.count(),
            2,
        )