from __future__ import annotations

import pytest

from agents.agent import TutorAgent
from context_engine.tool_registry import build_default_registry
from llm.provider import LLMResponse
from mocks.fake_search_tool import fake_search_course_content
from mocks.fake_student_request import fake_non_graded_question
from orchestrator.router import ChatRequest, Orchestrator
from dotenv import load_dotenv
load_dotenv()

@pytest.mark.asyncio
async def test_orchestrator_routes_to_tutor_and_returns_reply(scripted_provider):
    provider = scripted_provider([LLMResponse(text="Hi! Let's dig into that.", tool_calls=[])])
    registry = build_default_registry(fake_search_course_content)
    agent = TutorAgent(provider=provider, tool_registry=registry)
    orchestrator = Orchestrator(tutor_agent=agent)

    request = ChatRequest(question="Hello", raw_context=fake_non_graded_question())
    reply = await orchestrator.handle(request)

    assert reply.text == "Hi! Let's dig into that."