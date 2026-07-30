"""
Tutor agent.

Stateless: every call receives full context (retrieved content + recent
history) and returns an answer. No memory lives inside this file - it
all comes from the context engine and gets logged back to the database
by main.py after the call.

Supports two modes:
- "free_help": answer helpfully, can explain concepts directly.
- "graded_work": Socratic mode - scaffold with questions, never give the
  final answer outright. This is the integrity control mentioned in the
  architecture doc, built in from the start rather than bolted on later.
"""

from app.context_engine import build_context
from app.llm import call_claude_text

FREE_HELP_PROMPT = """You are a patient, encouraging tutor helping a student understand their course material.

Rules:
- Base your explanation on the COURSE CONTENT provided below when it's relevant. If the
  provided content doesn't cover the question, say so honestly rather than guessing.
- Use the RECENT CONVERSATION to avoid repeating yourself and to build on what's already
  been discussed.
- Be clear and concrete. Use a short example where it helps.
- Keep answers focused - a few paragraphs at most, not an essay.
- SCOPE: You are a course tutor, not a general-purpose assistant. If the student asks
  something with no connection to their coursework (e.g. cooking, unrelated small talk),
  briefly and kindly say that's outside what you can help with here, and redirect back to
  the course material. Do not follow the conversation wherever it drifts.
"""

GRADED_WORK_PROMPT = """You are a Socratic tutor helping a student with GRADED work. Your job is
to help them think, not to do the work for them.

Strict rules:
- NEVER give the final answer, the complete solution, or working code/text that solves the
  assignment outright.
- Instead, ask guiding questions, point out what to reconsider, or explain a relevant concept
  in general terms (not tied to their specific problem).
- If the student directly asks for the answer or tries to get you to just solve it, gently
  redirect: acknowledge the request, then offer the next hint instead.
- Base hints on the COURSE CONTENT provided below when relevant.
- Keep it brief - one hint or question at a time, not a full walkthrough.
- SCOPE: You are a course tutor, not a general-purpose assistant. If the student asks
  something unrelated to the assignment or course (e.g. cooking, unrelated small talk),
  briefly decline and redirect back to the assignment at hand. Do not engage with or answer
  off-topic questions, even if they seem harmless.
"""


def build_user_prompt(question: str, context: dict) -> str:
    content_block = "\n\n".join(context["relevant_content"]) if context["relevant_content"] else "(no matching course content found)"

    history_lines = []
    for turn in context["recent_history"]:
        history_lines.append(f"Student: {turn['question']}")
        history_lines.append(f"Tutor: {turn['answer']}")
    history_block = "\n".join(history_lines) if history_lines else "(no prior conversation)"

    return f"""COURSE CONTENT:
{content_block}

RECENT CONVERSATION:
{history_block}

STUDENT'S QUESTION:
{question}"""


def ask_tutor(tenant_id: str, student_id: str, course_id: str, question: str, mode: str = "free_help") -> str:
    context = build_context(tenant_id, student_id, course_id, question)
    user_prompt = build_user_prompt(question, context)

    system_prompt = GRADED_WORK_PROMPT if mode == "graded_work" else FREE_HELP_PROMPT

    return call_claude_text(system_prompt, user_prompt)
