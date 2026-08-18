"""
context_engine/build_context.py
Turns a raw request payload into a structured StudentContext the tutor agent
can use  who the student is, what course/lesson they're in, and whether
this is graded work.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QuizHistoryEntry:
    lesson_id: str
    score: float
    topic: str


@dataclass
class StudentContext:
    """Everything the tutor needs to know about who it's talking to, assembled once per request."""

    tenant_id: str
    student_id: str
    student_name: str
    course_id: str
    course_name: str
    lesson_id: str
    lesson_name: str
    is_graded_assignment: bool
    recent_quiz_history: list[QuizHistoryEntry] = field(default_factory=list)

    def as_prompt_block(self) -> str:
        """The cheap, always-relevant chunk that gets pushed straight into the system prompt."""
        history_lines = "\n".join(
            f"  - {q.topic}: {q.score:.0f}%" for q in self.recent_quiz_history
        ) or "  - no recent quiz history"

        return (
            f"Student: {self.student_name} (id: {self.student_id})\n"
            f"Course: {self.course_name} (id: {self.course_id})\n"
            f"Current lesson: {self.lesson_name} (id: {self.lesson_id})\n"
            f"This is graded work: {self.is_graded_assignment}\n"
            f"Recent quiz performance:\n{history_lines}"
        )


def build_student_context(raw: dict[str, Any]) -> StudentContext:
    """
    Turns a raw request payload (from the gateway, or
    mocks/fake_student_request.py during standalone development) into a
    structured StudentContext.
    """
    return StudentContext(
        tenant_id=raw["tenant_id"],
        student_id=raw["student_id"],
        student_name=raw.get("student_name", "Student"),
        course_id=raw["course_id"],
        course_name=raw.get("course_name", "Unknown course"),
        lesson_id=raw["lesson_id"],
        lesson_name=raw.get("lesson_name", "Unknown lesson"),
        is_graded_assignment=raw.get("is_graded_assignment", False),
        recent_quiz_history=[
            QuizHistoryEntry(**q) for q in raw.get("recent_quiz_history", [])
        ],
    )