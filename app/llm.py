"""
LLM wrapper.

This is the ONLY file in the app that talks to a language model.
Keeping it isolated here is what makes the model "swappable" - the
rest of the app (agents, routes) never knows or cares which provider
is actually answering.

Three providers, chosen by LLM_PROVIDER in .env:

  - "mock"      : no model at all, returns canned fake text. Good for
                  testing routes/database/context engine with zero setup.
  - "ollama"    : calls a model running locally via Ollama. Free, no API
                  key, runs entirely on your machine. Good for testing
                  real agent behavior before you commit to a paid key.
  - "anthropic" : calls the real Claude API. What you'll use once you
                  want production-quality answers and have working credits.

If LLM_PROVIDER isn't set, it auto-detects: Anthropic if a key is present,
otherwise mock.
"""

import os
import json
import requests
from anthropic import Anthropic

_client = None


def get_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider in ("mock", "ollama", "anthropic"):
        return provider
    # Auto-detect if not explicitly set
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "mock"


def get_client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set, but LLM_PROVIDER is 'anthropic'. "
                "Either add a real key to .env, or set LLM_PROVIDER=ollama or mock."
            )
        _client = Anthropic(api_key=api_key)
    return _client


# ---- Public functions used by the agents ----

def call_claude_json(system_prompt: str, user_prompt: str, max_tokens: int = 1500) -> dict:
    """Calls the configured provider and expects a JSON object back."""
    raw_text = _call_provider(system_prompt, user_prompt, max_tokens, expect_json=True)
    if isinstance(raw_text, dict):
        return raw_text  # mock mode already returns a dict directly
    return _parse_json(raw_text)


def call_claude_text(system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
    """Calls the configured provider and returns plain text (used by the Tutor agent)."""
    result = _call_provider(system_prompt, user_prompt, max_tokens, expect_json=False)
    return result


# ---- Provider dispatch ----

def _call_provider(system_prompt: str, user_prompt: str, max_tokens: int, expect_json: bool):
    provider = get_provider()

    if provider == "mock":
        return _mock_json_response(user_prompt) if expect_json else _mock_text_response(user_prompt)

    if provider == "ollama":
        return _call_ollama(system_prompt, user_prompt)

    # anthropic
    client = get_client()
    model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    """
    Calls a locally running Ollama server. Requires Ollama to be running
    (`ollama serve`, usually automatic) and the model already pulled
    (`ollama pull <model-name>`).
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3")

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Could not reach Ollama at {base_url}. Is it running? Try `ollama serve` "
            f"in a terminal, and make sure the model is pulled (`ollama pull {model}`)."
        )

    data = response.json()
    return data["message"]["content"]


def _parse_json(raw_text: str) -> dict:
    # Models sometimes wrap JSON in ```json fences despite instructions - strip them.
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {raw_text[:500]}") from e


# ---- Mock responses ----

def _mock_json_response(user_prompt: str) -> dict:
    return {
        "criteria_scores": [
            {"criterion": "Correctness", "score": 8, "max_score": 10,
             "feedback": "[MOCK MODE] This is a fake response so you can test the plumbing."},
            {"criterion": "Code style", "max_score": 5, "score": 4,
             "feedback": "[MOCK MODE] Set LLM_PROVIDER=ollama or anthropic in .env for real grading."},
        ],
        "total_score": 12,
        "max_total_score": 15,
        "overall_feedback": "[MOCK MODE] This is a placeholder grade, not a real one."
    }


def _mock_text_response(user_prompt: str) -> str:
    return (
        "[MOCK MODE] This is a placeholder answer so you can test the routes, database, "
        "and context engine without a real model yet. Set LLM_PROVIDER=ollama in .env to "
        "use your local Ollama model for free, or LLM_PROVIDER=anthropic with a real key."
    )
