from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import Choice, Question, Quiz, QuizAttempt, QuizAttemptAnswer


class ChoiceInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors) or self.instance.question_type != Question.QuestionType.MULTIPLE_CHOICE:
            return
        choices = [
            form.cleaned_data
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get("DELETE", False)
        ]
        if len(choices) < 2:
            raise ValidationError("A multiple-choice question needs at least two choices.")
        if sum(bool(choice.get("is_correct")) for choice in choices) != 1:
            raise ValidationError(
                "A multiple-choice question must have exactly one correct choice."
            )


class ChoiceInline(admin.TabularInline):
    model = Choice
    formset = ChoiceInlineFormSet
    extra = 2
    fields = ("text", "is_correct", "order")


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "difficulty", "is_active", "updated_at")
    list_filter = ("difficulty", "is_active")
    search_fields = ("title",)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "quiz", "question_type", "order")
    list_filter = ("quiz", "question_type")
    search_fields = ("text", "quiz__title")
    list_select_related = ("quiz",)
    inlines = (ChoiceInline,)
    readonly_fields = ("id", "created_at", "updated_at")


class SubmittedAnswerInline(admin.TabularInline):
    model = QuizAttemptAnswer
    extra = 0
    can_delete = False
    fields = ("question_text", "choice_text", "correct_choice_text", "is_correct")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "quiz_title_snapshot", "score", "completed_at")
    list_filter = ("completed_at",)
    search_fields = ("user__email", "quiz_title_snapshot")
    list_select_related = ("user",)
    inlines = (SubmittedAnswerInline,)
    readonly_fields = tuple(field.name for field in QuizAttempt._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
