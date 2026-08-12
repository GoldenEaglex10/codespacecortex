
"""
llm/provider.py

The swappable model layer. Every provider (Claude, ChatGPT, Gemini, DeepSeek)
is wrapped behind the same LLMProvider interface, so agents/tutor/agent.py
never needs to know which model is actually answering.

DeepSeek is covered by OpenAICompatibleProvider because DeepSeek's API is
OpenAI-compatible same request/response shape, just a different base_url
and API key.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

ProviderName = Literal["claude", "chatgpt", "gemini", "deepseek"]


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"
    raw: Any = None

    @property
    def wants_tool_call(self) -> bool:
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """Common interface every model provider adapter must implement."""

    name: str

    @abstractmethod
    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        ...


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self, model: str = "claude-sonnet-4-6", api_key: str | None = None):
        from anthropic import AsyncAnthropic

        self.model = model
        self.client = AsyncAnthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])

    async def complete(self, *, system, messages, tools=None, max_tokens=1024) -> LLMResponse:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            tools=tools or [],
        )

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, input=block.input))

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            raw=response,
        )


class OpenAICompatibleProvider(LLMProvider):
    """
    Covers both ChatGPT and DeepSeek, since DeepSeek's API is OpenAI-compatible.
    Only the base_url, api_key and model differ between the two.
    """

    def __init__(self, *, provider_name: str, model: str, base_url: str | None, api_key: str):
        from openai import AsyncOpenAI

        self.name = provider_name
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def complete(self, *, system, messages, tools=None, max_tokens=1024) -> LLMResponse:
        openai_messages = [{"role": "system", "content": system}, *messages]

        openai_tools = None
        if tools:
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "parameters": t.get("input_schema", {}),
                    },
                }
                for t in tools
            ]

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            tools=openai_tools,
            max_tokens=max_tokens,
        )

        choice = response.choices[0]
        text = choice.message.content or ""
        tool_calls: list[ToolCall] = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        input=json.loads(tc.function.arguments or "{}"),
                    )
                )

        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason,
            raw=response,
        )


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, model: str = "gemini-2.5-pro", api_key: str | None = None):
        from google import genai

        self.model = model
        self.client = genai.Client(api_key=api_key or os.environ["GEMINI_API_KEY"])

    async def complete(self, *, system, messages, tools=None, max_tokens=1024) -> LLMResponse:
        from google.genai import types

        contents = []
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=m["content"])]))

        gemini_tools = None
        if tools:
            declarations = [
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t.get("description", ""),
                    parameters=t.get("input_schema", {}),
                )
                for t in tools
            ]
            gemini_tools = [types.Tool(function_declarations=declarations)]

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system,
                tools=gemini_tools,
                max_output_tokens=max_tokens,
            ),
        )

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        candidate = response.candidates[0]
        for part in candidate.content.parts:
            if getattr(part, "text", None):
                text_parts.append(part.text)
            if getattr(part, "function_call", None):
                fc = part.function_call
                tool_calls.append(ToolCall(id=fc.name, name=fc.name, input=dict(fc.args)))

        stop_reason = candidate.finish_reason.name if candidate.finish_reason else "end_turn"

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            raw=response,
        )


def get_provider(name: ProviderName) -> LLMProvider:
    """
    Factory — the single place that knows how to build each provider.
    This is what the orchestrator/router calls when deciding which model
    should handle a given request (model routing).
    """
    if name == "claude":
        return ClaudeProvider()
    if name == "chatgpt":
        return OpenAICompatibleProvider(
            provider_name="chatgpt",
            model=os.environ.get("OPENAI_MODEL", "gpt-4.1"),
            base_url=None,
            api_key=os.environ["OPENAI_API_KEY"],
        )
    if name == "deepseek":
        return OpenAICompatibleProvider(
            provider_name="deepseek",
            model=os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url="https://api.deepseek.com",
            api_key=os.environ["DEEPSEEK_API_KEY"],
        )
    if name == "gemini":
        return GeminiProvider()
    raise ValueError(f"Unknown provider: {name}")