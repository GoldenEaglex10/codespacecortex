"""
Content agent (Phase 2, Step 2).

Given a topic and a content type, generates teacher-facing material -
right now: quizzes. Grounded in whatever course content has already been
ingested for that course (reuses the same retrieval the Tutor agent uses),
so questions are based on what was actually taught, not generic trivia.

Structured output, same pattern as the Assessment agent: force JSON,
parse it, hand back something a UI could render directly.
"""

from app.llm import call_claude_json
from app.context_engine import retrieve_relevant_content

QUIZ_SYSTEM_PROMPT = """You are an experienced teacher creating a quiz for your students.

Rules you must follow:
- Base every question on the COURSE CONTENT provided. Do not invent facts or ask about
  things not covered in the content.
- Vary difficulty: include a mix of straightforward recall and questions that require
  applying the concept, unless a difficulty level is specified.
- Each question must have exactly one clearly correct answer among the options.
- Write plausible wrong answers (distractors) - not obviously silly ones.
- Include a short explanation for why the correct answer is correct.
- Respond with ONLY a JSON object, no other text, no markdown fences, matching exactly
  this shape:

{
  "quiz_title": "<short descriptive title>",
  "questions": [
    {
      "question": "<question text>",
      "options": ["<option A>", "<option B>", "<option C>", "<option D>"],
      "correct_answer_index": <0-3>,
      "explanation": "<why this is correct, 1-2 sentences>"
    }
  ]
}
"""


def build_quiz_prompt(topic: str, course_content: list, num_questions: int, difficulty: str) -> str:
    if course_content:
        content_block = "\n\n".join(course_content)
    else:
        content_block = "(no matching course content was found - write general, clearly-labeled placeholder questions and note in each explanation that no source material was available)"

    return f"""COURSE CONTENT:
{content_block}

TASK: Create a {num_questions}-question multiple-choice quiz on the topic "{topic}".
Difficulty level: {difficulty}.

Respond with the JSON object only."""


def generate_quiz(tenant_id: str, course_id: str, topic: str,
                   num_questions: int = 5, difficulty: str = "mixed") -> dict:
    course_content = retrieve_relevant_content(tenant_id, course_id, topic, top_k=5)
    content_texts = [c["chunk_text"] for c in course_content]

    user_prompt = build_quiz_prompt(topic, content_texts, num_questions, difficulty)
    result = call_claude_json(QUIZ_SYSTEM_PROMPT, user_prompt)
    return result
