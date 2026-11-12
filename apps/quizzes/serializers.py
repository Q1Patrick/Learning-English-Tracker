"""Public quiz schemas omit correct answers before submission."""

from rest_framework import serializers

from .models import Choice, Question, Quiz, QuizAttempt, QuizAttemptAnswer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text", "order")
        read_only_fields = fields


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "question_type", "order", "choices")
        read_only_fields = fields


class QuizListSerializer(serializers.ModelSerializer):
    question_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "title", "description", "difficulty", "question_count")
        read_only_fields = fields


class QuizDetailSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ("id", "title", "description", "difficulty", "questions")
        read_only_fields = fields


class SubmittedAnswerSerializer(serializers.Serializer):
    question_id = serializers.UUIDField()
    choice_id = serializers.UUIDField()


class QuizSubmissionSerializer(serializers.Serializer):
    answers = SubmittedAnswerSerializer(many=True, min_length=1, max_length=1000)

    def validate_answers(self, answers):
        ids = [answer["question_id"] for answer in answers]
        if len(ids) != len(set(ids)):
            raise serializers.ValidationError(
                "Each question must be answered exactly once.", code="duplicate_answer"
            )
        return answers


class QuizAttemptAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.UUIDField(source="question_id_snapshot")
    choice_id = serializers.UUIDField(source="choice_id_snapshot")
    correct_choice_id = serializers.UUIDField(source="correct_choice_id_snapshot")

    class Meta:
        model = QuizAttemptAnswer
        fields = (
            "question_id",
            "choice_id",
            "correct_choice_id",
            "question_text",
            "choice_text",
            "correct_choice_text",
            "explanation",
            "is_correct",
            "order",
        )
        read_only_fields = fields


class QuizAttemptListSerializer(serializers.ModelSerializer):
    quiz_id = serializers.UUIDField(source="quiz_id_snapshot", allow_null=True)
    quiz_title = serializers.CharField(source="quiz_title_snapshot")

    class Meta:
        model = QuizAttempt
        fields = (
            "id",
            "quiz_id",
            "quiz_title",
            "score",
            "correct_answers",
            "total_questions",
            "completed_at",
        )
        read_only_fields = fields


class QuizAttemptDetailSerializer(QuizAttemptListSerializer):
    answers = QuizAttemptAnswerSerializer(many=True, read_only=True)

    class Meta(QuizAttemptListSerializer.Meta):
        fields = QuizAttemptListSerializer.Meta.fields + ("answers",)
        read_only_fields = fields
