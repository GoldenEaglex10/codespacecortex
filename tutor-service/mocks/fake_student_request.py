
from __future__ import annotations

from typing import Any


def fake_non_graded_question() -> dict[str, Any]:
    return {
        "tenant_id": "tenant_demo_school",
        "student_id": "student_001",
        "student_name": "Tafara",
        "course_id": "course_python_101",
        "course_name": "Python 101",
        "lesson_id": "lesson_04",
        "lesson_name": "OOP Concepts",
        "is_graded_assignment": False,
        "recent_quiz_history": [
            {"lesson_id": "lesson_03", "score": 82.0, "topic": "Functions"},
        ],
    }


def fake_graded_question() -> dict[str, Any]:
    data = fake_non_graded_question()
    data["is_graded_assignment"] = True
    return data