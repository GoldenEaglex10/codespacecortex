from __future__ import annotations

import re

from context_engine.build_context import StudentContext

# Phrases that suggest the model is handing over a direct final answer
# instead of guiding.
_DIRECT_ANSWER_MARKERS = [
    r"\bthe answer is\b",
    r"\bthe solution is\b",
    r"\bthe correct answer is\b",
    r"\bhere is (the )?(complete|full|final) (code|solution|answer)\b",
    r"\bjust copy\b",
    r"\bthe result is\b",
]

_FALLBACK_REDIRECT = (
    "I can see you're working on graded material, so instead of giving you the final "
    "answer directly, let's work through it together. What have you tried so far, "
    "or which part of the problem are you stuck on? Let's break it down step by step."
)


def looks_like_direct_answer(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _DIRECT_ANSWER_MARKERS)


def enforce_pedagogy(reply_text: str, context: StudentContext) -> str:
    """
    If this is graded work and the reply looks like it just handed over the
    answer, redirect to a more pedagogical response instead of sending it
    to the student as is.
    """
    if context.is_graded_assignment and looks_like_direct_answer(reply_text):
        return _FALLBACK_REDIRECT
    return reply_text