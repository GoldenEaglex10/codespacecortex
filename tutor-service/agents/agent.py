from __future__ import annotations
from dataclasses import dataclass, field
from agents.pedagogy import enforce_pedagogy
from agents.prompts import build_system_prompt
from context_engine.build_context import StudentContext
from context_engine.tool_registry import ToolRegistry
from llm.provider import LLMProvider, ToolCall

MAX_TOOL_ITERATIONS = 3


@dataclass
class TutorReplay:
    text: str
    tools_used: list[str] = field(default_factory=list)


class TutorAgent:
    def __init__(self, provider: LLMProvider, tool_registry: ToolRegistry):
        self.provider = provider
        self.tool_registry = tool_registry

    async def respond(self, *, question: str, context: StudentContext) -> TutorReplay:
        system = build_system_prompt(context=context)
        messages: list[dict] = [{"role": "user", "content": question}]
        tools_used: list[str] = []
        response = None

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await self.provider.complete(
                system=system,
                messages=messages,
                tools=self.tool_registry.provider_schemas(),
            )

            if not response.wants_tool_call:
                final_text = enforce_pedagogy(response.text, context=context)
                return TutorReplay(text=final_text, tools_used=tools_used)

            # model wants to call one or more tools  this must be INSIDE the loop
            messages.append({"role": "assistant", "content": response.text or ""})
            for call in response.tool_calls:
                tools_used.append(call.name)
                result = await self._run_tool(call)
                messages.append(
                    {"role": "user", "content": f"Tool {call.name} returned: {result}"}
                )

        # ran out of tool call iterations  return whatever text we have,
        # still pedagogy checked, rather than looping forever
        fallback_text = (response.text if response else "") or (
            "I wasn't able to fully answer that  could you rephrase?"
        )
        final_text = enforce_pedagogy(fallback_text, context=context)
        return TutorReplay(text=final_text, tools_used=tools_used)

    async def _run_tool(self, call: ToolCall) -> str:
        try:
            result = await self.tool_registry.execute(call.name, call.input)
            return str(result)
        except Exception as e:
            return f"Error running tool {call.name}: {e}"