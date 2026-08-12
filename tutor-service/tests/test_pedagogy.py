from __future__ import annotations

from agents.pedagogy import enforce_pedagogy, looks_like_direct_answer
from context_engine.build_context import build_student_context
from mocks.fake_student_reqeust import fake_graded_question, fake_non_graded_question


def test_detects_direct_answer_phrases():
    assert looks_like_direct_answer("The answer is 42.")
    assert looks_like_direct_answer("Here is the complete solution:")
    assert not looks_like_direct_answer("Have you thought about what the first step might be?")


def test_non_graded_work_is_not_touched():
    context = build_student_context(fake_non_graded_question())
    text = "The answer is 42."
    assert enforce_pedagogy(text, context) == text


def test_graded_work_gets_redirected():
    context = build_student_context(fake_graded_question())
    text = "The answer is 42."
    result = enforce_pedagogy(text, context)
    assert result != text
    assert "let's work through it together" in result.lower()