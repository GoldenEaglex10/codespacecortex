

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agents.agent import TutorAgent, TutorReply
from context_engine.build_context import build_student_context


@dataclass
class ChatRequest:
    """What the gateway hands the orchestrator for a single chat turn."""

    question: str
    raw_context: dict[str, Any]


class Orchestrator:
    def __init__(self, tutor_agent: TutorAgent):
        self.tutor_agent = tutor_agent

    async def handle(self, request: ChatRequest) -> TutorReply:
        context = build_student_context(request.raw_context)
        # Future: inspect request/context to decide which agent handles this.
        # For Phase 1, everything goes to the tutor.
        return await self.tutor_agent.respond(question=request.question, context=context)