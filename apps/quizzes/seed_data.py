"""Versioned development content; changing a version creates a new sample quiz.

Stable UUIDs identify seed-owned quizzes without reserving titles or overwriting
an existing quiz. Every topic uses the currently supported multiple-choice type.
"""

from dataclasses import dataclass
from typing import Tuple
from uuid import UUID, uuid5

SEED_NAMESPACE = UUID("434ef8bf-531b-4ce5-84f4-d9ffec6b4911")


@dataclass(frozen=True)
class ChoiceSeed:
    text: str
    is_correct: bool = False


@dataclass(frozen=True)
class QuestionSeed:
    slug: str
    text: str
    explanation: str
    choices: Tuple[ChoiceSeed, ...]


@dataclass(frozen=True)
class QuizSeed:
    slug: str
    title: str
    description: str
    difficulty: str
    questions: Tuple[QuestionSeed, ...]
    version: int = 1


def seed_uuid(seed: QuizSeed, *parts: str) -> UUID:
    """IDs depend on version and stable slugs/positions, never database state."""
    return uuid5(SEED_NAMESPACE, "/".join((seed.slug, f"v{seed.version}", *parts)))


QUIZ_SEEDS = (
    QuizSeed(
        slug="everyday-vocabulary",
        title="Everyday Vocabulary",
        description="Practise useful words for everyday situations.",
        difficulty="beginner",
        questions=(
            QuestionSeed(
                slug="borrow",
                text='Which sentence uses "borrow" correctly?',
                explanation="Borrow means receive something temporarily and return it later.",
                choices=(
                    ChoiceSeed("Can I borrow your pen for a moment?", True),
                    ChoiceSeed("Can I borrow you my pen?"),
                    ChoiceSeed("I borrow my pen to my friend."),
                    ChoiceSeed("I borrow a pen forever and never return it."),
                ),
            ),
            QuestionSeed(
                slug="crowded",
                text="A bus is full of people. Which word best describes it?",
                explanation="A crowded place has many people and little free space.",
                choices=(
                    ChoiceSeed("Empty"),
                    ChoiceSeed("Crowded", True),
                    ChoiceSeed("Silent"),
                    ChoiceSeed("Private"),
                ),
            ),
            QuestionSeed(
                slug="receipt",
                text="What do you call the document showing what you paid for in a shop?",
                explanation="A receipt records a completed purchase and its payment.",
                choices=(
                    ChoiceSeed("A menu"),
                    ChoiceSeed("A timetable"),
                    ChoiceSeed("A receipt", True),
                    ChoiceSeed("A passport"),
                ),
            ),
        ),
    ),
    QuizSeed(
        slug="grammar-foundations",
        title="Grammar Foundations",
        description="Choose the correct verb form, article and comparison.",
        difficulty="beginner",
        questions=(
            QuestionSeed(
                slug="past-tense",
                text="Yesterday, she ___ to the library.",
                explanation="Yesterday refers to the past; the past tense of go is went.",
                choices=(
                    ChoiceSeed("go"),
                    ChoiceSeed("goes"),
                    ChoiceSeed("going"),
                    ChoiceSeed("went", True),
                ),
            ),
            QuestionSeed(
                slug="article",
                text="He is ___ engineer.",
                explanation="Use an before a singular countable noun beginning with a vowel sound.",
                choices=(
                    ChoiceSeed("an", True),
                    ChoiceSeed("a"),
                    ChoiceSeed("many"),
                    ChoiceSeed("no article"),
                ),
            ),
            QuestionSeed(
                slug="comparison",
                text="This book is ___ than the one I read last week.",
                explanation="The comparative form of interesting is more interesting.",
                choices=(
                    ChoiceSeed("most interesting"),
                    ChoiceSeed("more interesting", True),
                    ChoiceSeed("interestinger"),
                    ChoiceSeed("as interesting"),
                ),
            ),
        ),
    ),
    QuizSeed(
        slug="phrasal-verbs-basics",
        title="Phrasal Verbs Basics",
        description="Learn common phrasal verbs in a clear context.",
        difficulty="intermediate",
        questions=(
            QuestionSeed(
                slug="figure-out",
                text='In "I finally figured out the answer", what does "figure out" mean?',
                explanation="Figure out means understand or solve something.",
                choices=(
                    ChoiceSeed("Forget completely"),
                    ChoiceSeed("Write more neatly"),
                    ChoiceSeed("Understand or solve", True),
                    ChoiceSeed("Leave immediately"),
                ),
            ),
            QuestionSeed(
                slug="put-off",
                text="They put off the meeting until Friday. What did they do?",
                explanation="Put off an event means postpone it to a later time.",
                choices=(
                    ChoiceSeed("Cancelled it permanently"),
                    ChoiceSeed("Started it early"),
                    ChoiceSeed("Made it longer"),
                    ChoiceSeed("Postponed it", True),
                ),
            ),
            QuestionSeed(
                slug="take-on",
                text="She agreed to take on a new responsibility. What did she agree to do?",
                explanation="Take on a responsibility means accept it.",
                choices=(
                    ChoiceSeed("Accept a new duty", True),
                    ChoiceSeed("Refuse all work"),
                    ChoiceSeed("Finish every task immediately"),
                    ChoiceSeed("Give the responsibility away"),
                ),
            ),
        ),
    ),
    QuizSeed(
        slug="beginner-english",
        title="Beginner English Check",
        description="Practise greetings, personal information and everyday questions.",
        difficulty="beginner",
        questions=(
            QuestionSeed(
                slug="greeting",
                text='Which is the most natural reply to "How are you?"?',
                explanation="I'm fine, thanks is a common polite reply about how you feel.",
                choices=(
                    ChoiceSeed("I am twenty years old."),
                    ChoiceSeed("I'm fine, thanks.", True),
                    ChoiceSeed("It is on the table."),
                    ChoiceSeed("My name is a book."),
                ),
            ),
            QuestionSeed(
                slug="be-verb",
                text="They ___ students.",
                explanation="Use are with the subject they in the present tense.",
                choices=(
                    ChoiceSeed("am"),
                    ChoiceSeed("is"),
                    ChoiceSeed("are", True),
                    ChoiceSeed("be"),
                ),
            ),
            QuestionSeed(
                slug="place-question",
                text="Which question asks about someone's home location?",
                explanation="Where asks about a place; Where do you live? asks about home location.",
                choices=(
                    ChoiceSeed("When do you sleep?"),
                    ChoiceSeed("How old are you?"),
                    ChoiceSeed("What do you eat?"),
                    ChoiceSeed("Where do you live?", True),
                ),
            ),
        ),
    ),
    QuizSeed(
        slug="intermediate-english",
        title="Intermediate English Check",
        description="Practise present perfect, conditionals and natural word combinations.",
        difficulty="intermediate",
        questions=(
            QuestionSeed(
                slug="present-perfect",
                text="I ___ here since 2020, and I still live here.",
                explanation="Use present perfect for a situation that began in the past and continues now.",
                choices=(
                    ChoiceSeed("have lived", True),
                    ChoiceSeed("live yesterday"),
                    ChoiceSeed("am live"),
                    ChoiceSeed("will lived"),
                ),
            ),
            QuestionSeed(
                slug="first-conditional",
                text="If it rains tomorrow, we ___ at home.",
                explanation="The first conditional uses if + present simple, followed by will + verb.",
                choices=(
                    ChoiceSeed("stayed"),
                    ChoiceSeed("will stay", True),
                    ChoiceSeed("would stayed"),
                    ChoiceSeed("staying"),
                ),
            ),
            QuestionSeed(
                slug="collocation",
                text="After discussing our options, we need to ___ a decision.",
                explanation="Make a decision is the usual English word combination.",
                choices=(
                    ChoiceSeed("do"),
                    ChoiceSeed("give"),
                    ChoiceSeed("make", True),
                    ChoiceSeed("build"),
                ),
            ),
        ),
    ),
)
