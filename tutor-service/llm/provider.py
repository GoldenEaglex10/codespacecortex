from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal


ProviderName = Literal["claude", "chatgpt", "gemini", "deepseek"]



# Shared response models


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



# Provider interface


class LLMProvider(ABC):
    """
    Common interface every model provider adapter must implement.
    """

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
        raise NotImplementedError


# Claude / Anthropic


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(
        self,
        model: str = "claude-sonnet-4-6",
        api_key: str | None = None,
    ):
        from anthropic import AsyncAnthropic

        self.model = model

        self.client = AsyncAnthropic(
            api_key=api_key or os.environ["ANTHROPIC_API_KEY"]
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:

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
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        input=block.input,
                    )
                )

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=response.stop_reason,
            raw=response,
        )



# OpenAIcompatible provider
#
# Used for:
#   - OpenAI / ChatGPT
#   - DeepSeek


class OpenAICompatibleProvider(LLMProvider):
    """
    Supports OpenAI-compatible APIs.

    DeepSeek exposes an OpenAI-compatible API, so the same
    implementation can be reused by changing:

        provider_name
        model
        base_url
        api_key
    """

    def __init__(
        self,
        *,
        provider_name: str,
        model: str,
        base_url: str | None,
        api_key: str,
    ):
        from openai import AsyncOpenAI

        self.name = provider_name
        self.model = model

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:

        openai_messages = [
            {
                "role": "system",
                "content": system,
            },
            *messages,
        ]

        openai_tools = None

        if tools:
            openai_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get(
                            "input_schema",
                            {},
                        ),
                    },
                }
                for tool in tools
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

            for tool_call in choice.message.tool_calls:

                try:
                    arguments = json.loads(
                        tool_call.function.arguments or "{}"
                    )
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls.append(
                    ToolCall(
                        id=tool_call.id,
                        name=tool_call.function.name,
                        input=arguments,
                    )
                )

        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason,
            raw=response,
        )



# Gemini


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ):
        from google import genai

        self.model = model or os.environ.get(
            "GEMINI_MODEL",
            "gemini-3.5-flash-lite",
        )

        self.fallback_model = os.environ.get(
            "GEMINI_FALLBACK_MODEL",
            "gemini-2.5-flash",
        )

        self.client = genai.Client(
            api_key=api_key or os.environ["GEMINI_API_KEY"]
        )

   
    # Build Gemini contents
   

    def _build_contents(
        self,
        messages: list[dict[str, Any]],
    ):
        from google.genai import types

        contents = []

        for message in messages:

            role = message.get("role", "user")

            # Gemini uses "model" instead of "assistant".
            gemini_role = (
                "model"
                if role == "assistant"
                else "user"
            )

            content = message.get("content", "")

            # Normal text message.
            if isinstance(content, str):

                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[
                            types.Part.from_text(
                                text=content
                            )
                        ],
                    )
                )

            else:
                # Defensive fallback.
                contents.append(
                    types.Content(
                        role=gemini_role,
                        parts=[
                            types.Part.from_text(
                                text=str(content)
                            )
                        ],
                    )
                )

        return contents

    
    # Build Gemini tools
   

    def _build_tools(
        self,
        tools: list[dict[str, Any]] | None,
    ):
        from google.genai import types

        if not tools:
            return None

        declarations = []

        for tool in tools:

            declarations.append(
                types.FunctionDeclaration(
                    name=tool["name"],
                    description=tool.get(
                        "description",
                        "",
                    ),
                    parameters=tool.get(
                        "input_schema",
                        {},
                    ),
                )
            )

        return [
            types.Tool(
                function_declarations=declarations
            )
        ]

 
    # Make one Gemini request
   

    async def _generate(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        max_tokens: int,
    ) -> LLMResponse:

        from google.genai import types

        contents = self._build_contents(messages)

        gemini_tools = self._build_tools(tools)

        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=gemini_tools,
            max_output_tokens=max_tokens,
        )

        response = await self.client.aio.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        
        # Defensive response validation
        

        if not response.candidates:
            raise RuntimeError(
                f"Gemini returned no candidates. "
                f"Model={model}"
            )

        candidate = response.candidates[0]

        if candidate.content is None:
            return LLMResponse(
                text="",
                tool_calls=[],
                stop_reason="end_turn",
                raw=response,
            )

        text_parts: list[str] = []

        tool_calls: list[ToolCall] = []

        for part in candidate.content.parts:

            # Text response.
            text = getattr(part, "text", None)

            if text:
                text_parts.append(text)

            # Function call.
            function_call = getattr(
                part,
                "function_call",
                None,
            )

            if function_call:

                tool_calls.append(
                    ToolCall(
                        id=function_call.name,
                        name=function_call.name,
                        input=dict(
                            function_call.args or {}
                        ),
                    )
                )

        finish_reason = getattr(
            candidate,
            "finish_reason",
            None,
        )

        if finish_reason is not None:
            stop_reason = getattr(
                finish_reason,
                "name",
                str(finish_reason),
            )
        else:
            stop_reason = "end_turn"

        return LLMResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            raw=response,
        )

    
    # Public completion method
 

    async def complete(
        self,
        *,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1024,
    ) -> LLMResponse:

        try:

            return await self._generate(
                model=self.model,
                system=system,
                messages=messages,
                tools=tools,
                max_tokens=max_tokens,
            )

        except Exception as exc:

            # Google GenAI errors expose the HTTP status through
            # the exception. We only fallback for transient
            # availability/rate-limit errors.
            status_code = getattr(
                exc,
                "status_code",
                None,
            )

            if status_code is None:
                status_code = getattr(
                    exc,
                    "code",
                    None,
                )

            # Do not fallback for authentication, invalid request,
            # permission, etc.
            if status_code not in (429, 500, 503, 504):
                raise

            # Avoid recursively falling back to the same model.
            if self.fallback_model == self.model:
                raise

            print(
                f"[Gemini] Primary model '{self.model}' "
                f"returned HTTP {status_code}. "
                f"Trying fallback model "
                f"'{self.fallback_model}'."
            )

            return await self._generate(
                model=self.fallback_model,
                system=system,
                messages=messages,
                tools=tools,
                max_tokens=max_tokens,
            )



# Provider factory


def get_provider(name: ProviderName) -> LLMProvider:
    """
    Central provider factory.

    The orchestrator/router should call this function instead
    of constructing provider clients directly.
    """

    if name == "claude":

        return ClaudeProvider()

    if name == "chatgpt":

        return OpenAICompatibleProvider(
            provider_name="chatgpt",
            model=os.environ.get(
                "OPENAI_MODEL",
                "gpt-4.1",
            ),
            base_url=None,
            api_key=os.environ[
                "OPENAI_API_KEY"
            ],
        )

    if name == "deepseek":

        return OpenAICompatibleProvider(
            provider_name="deepseek",
            model=os.environ.get(
                "DEEPSEEK_MODEL",
                "deepseek-chat",
            ),
            base_url="https://api.deepseek.com",
            api_key=os.environ[
                "DEEPSEEK_API_KEY"
            ],
        )

    if name == "gemini":

        return GeminiProvider()

    raise ValueError(
        f"Unknown provider: {name}"
    )