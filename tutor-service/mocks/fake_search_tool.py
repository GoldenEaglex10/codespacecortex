"""
mocks/fake_search_tool.py

Stand-in for Nyasha's real search_course_content tool. Same input/output
shape documented in context_engine/tool_registry.py — swap this executor
for the real one once it exists, without touching agent.py.
"""

from __future__ import annotations

from typing import Any

_FAKE_COURSE_CONTENT = {
    "polymorphism": [
        {
            "content": (
                "Polymorphism lets objects of different classes be treated through "
                "a common interface. In Python, this often shows up as different "
                "classes implementing the same method name."
            ),
            "source": "Lesson 4: OOP Concepts",
            "score": 0.92,
        },
    ],
    "recursion": [
        {
            "content": (
                "A recursive function is one that calls itself, with a base case "
                "that stops the recursion. Every recursive call should move closer "
                "to that base case."
            ),
            "source": "Lesson 6: Functions Deep Dive",
            "score": 0.88,
        },
    ],
}


async def fake_search_course_content(tool_input: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Signature matches what the real tool must satisfy:
    input:  {"query": str, "course_id": str | None}
    output: list[{"content": str, "source": str, "score": float}]
    """
    query = tool_input.get("query", "").lower()
    for keyword, results in _FAKE_COURSE_CONTENT.items():
        if keyword in query:
            return results
    return [
        {
            "content": "No matching course material found for this query.",
            "source": "n/a",
            "score": 0.0,
        }
    ]