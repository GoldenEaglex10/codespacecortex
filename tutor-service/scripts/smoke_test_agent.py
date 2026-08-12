"""
scripts/smoke_test_agent.py
Run the real tutor agent against a real provider + the fake search tool.
"""

import asyncio
from dotenv import load_dotenv
load_dotenv()

from agents.agent import TutorAgent
from context_engine.build_context import build_student_context
from context_engine.tool_registry import build_default_registry
from llm.provider import get_provider
from mocks.fake_search_tool import fake_search_course_content
from mocks.fake_student_request import fake_non_graded_question


async def main():
    provider = get_provider("gemini")  # or deepseek
    registry = build_default_registry(fake_search_course_content)
    agent = TutorAgent(provider=provider, tool_registry=registry)
    context = build_student_context(fake_non_graded_question())

    reply = await agent.respond(question="want to learn llms engineering with implementations", context=context)

    print("Reply text:", reply.text)
    print("Tools used:", reply.tools_used)


asyncio.run(main())