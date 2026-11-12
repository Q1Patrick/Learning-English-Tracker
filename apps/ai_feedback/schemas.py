from typing import List

from pydantic import BaseModel, Field


class MistakeSchema(BaseModel):
    original: str
    correction: str
    explanation: str


class EnglishFeedbackSchema(BaseModel):
    corrected_text: str
    overall_feedback: str

    grammar_score: int = Field(
        ge=0,
        le=100,
    )

    vocabulary_score: int = Field(
        ge=0,
        le=100,
    )

    clarity_score: int = Field(
        ge=0,
        le=100,
    )

    mistakes: List[MistakeSchema]
    suggestions: List[str]
