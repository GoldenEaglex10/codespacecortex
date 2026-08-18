"""
tests/conftest.py
"""

from __future__ import annotations

import pytest

from llm.provider import LLMProvider, LLMResponse


class ScriptedProvider(LLMProvider):
    name = "scripted"

    def __init__(self, responses: list[LLMResponse]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    async def complete(self, *, system, messages, tools=None, max_tokens=1024) -> LLMResponse:
        self.calls.append({"system": system, "messages": messages, "tools": tools})
        if not self._responses:
            raise AssertionError("ScriptedProvider ran out of scripted responses")
        return self._responses.pop(0)


@pytest.fixture
def scripted_provider():
    return ScriptedProvider