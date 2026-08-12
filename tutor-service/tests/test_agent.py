from __future__ import annotations

import pytest

from agents.agent import TutorAgent
from context_engine.build_context import build_student_context
from context_engine.tool_registry import build_default_registry
from llm.provider import LLMResponse, ToolCall
from mocks.fake_search_tool import fake_search_course_content
from mocks.fake_student_request import fake_graded_question, fake_non_graded_question


@pytest.mark.asyncio
async def test_direct_answer_when_no_tool_needed(scripted_provider):
    provider = scripted_provider(
        [LLMResponse(text="Sure — here's how classes work in Python...", tool_calls=[])]
    )
    registry = build_default_registry(fake_search_course_content)
    agent = TutorAgent(provider=provider, tool_registry=registry)
    context = build_student_context(fake_non_graded_question())

    reply = await agent.respond(question="What is a class?", context=context)

    assert "classes" in reply.text.lower()
    assert reply.tools_used == []


@pytest.mark.asyncio
async def test_agent_uses_tool_when_model_requests_it(scripted_provider):
    provider = scripted_provider(
        [
            LLMResponse(
                text="",
                tool_calls=[
                    ToolCall(id="1", name="search_course_content", input={"query": "polymorphism"})
                ],
            ),
            LLMResponse(text="Polymorphism means...", tool_calls=[]),
        ]
    )
    registry = build_default_registry(fake_search_course_content)
    agent = TutorAgent(provider=provider, tool_registry=registry)
    context = build_student_context(fake_non_graded_question())

    reply = await agent.respond(question="Explain polymorphism", context=context)

    assert reply.tools_used == ["search_course_content"]
    assert "polymorphism" in reply.text.lower()


@pytest.mark.asyncio
async def test_graded_work_direct_answer_gets_redirected(scripted_provider):
    provider = scripted_provider([LLMResponse(text="The answer is 42.", tool_calls=[])])
    registry = build_default_registry(fake_search_course_content)
    agent = TutorAgent(provider=provider, tool_registry=registry)
    context = build_student_context(fake_graded_question())

    reply = await agent.respond(question="What's the answer to question 3?", context=context)

    assert "the answer is 42" not in reply.text.lower()
    assert "let's work through it together" in reply.text.lower()


@pytest.mark.asyncio
async def test_stops_after_max_tool_iterations(scripted_provider):
    # Model keeps asking for tools forever — agent must not loop infinitely.
    looping_response = LLMResponse(
        text="",
        tool_calls=[ToolCall(id="x", name="search_course_content", input={"query": "recursion"})],
    )
    provider = scripted_provider([looping_response, looping_response, looping_response])
    registry = build_default_registry(fake_search_course_content)
    agent = TutorAgent(provider=provider, tool_registry=registry)
    context = build_student_context(fake_non_graded_question())

    reply = await agent.respond(question="Explain recursion", context=context)

    assert len(reply.tools_used) == 3
    assert reply.text  # got a fallback string, didn't crash