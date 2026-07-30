"""
Assessment agent.

Given a rubric and a student's submission, produces a structured grade:
a score per criterion plus written feedback per criterion, and an
overall summary. This is intentionally the FIRST agent built in Phase 2
because grading quality is the easiest thing for a teacher to judge as
"good" or "bad", which makes it the fastest feedback loop to tune.
"""

from app.llm import call_claude_json

SYSTEM_PROMPT = """You are an experienced, fair teaching assistant grading student work.

Rules you must follow:
- Grade ONLY against the rubric criteria given. Do not invent new criteria.
- Be consistent: the same quality of work should get the same score every time.
- Give specific, actionable feedback tied to the actual submission text - never generic
  praise or generic criticism.
- Be encouraging in tone, but honest about gaps. Do not inflate scores to be kind.
- Respond with ONLY a JSON object, no other text, no markdown fences, matching exactly
  this shape:

{
  "criteria_scores": [
    {"criterion": "<criterion name>", "score": <number>, "max_score": <number>, "feedback": "<specific feedback>"}
  ],
  "total_score": <number>,
  "max_total_score": <number>,
  "overall_feedback": "<2-4 sentences summarizing strengths and the single most important thing to improve>"
}
"""


def build_grading_prompt(submission_text: str, rubric: list) -> str:
    rubric_lines = []
    for item in rubric:
        rubric_lines.append(
            f"- {item['criterion']} (max {item['max_points']} points): {item['description']}"
        )
    rubric_block = "\n".join(rubric_lines)

    return f"""RUBRIC:
{rubric_block}

STUDENT SUBMISSION:
\"\"\"
{submission_text}
\"\"\"

Grade this submission against the rubric above. Respond with the JSON object only."""


def grade_submission(submission_text: str, rubric: list) -> dict:
    """
    rubric: list of {"criterion": str, "max_points": number, "description": str}
    Returns the parsed grading result dict.
    """
    user_prompt = build_grading_prompt(submission_text, rubric)
    result = call_claude_json(SYSTEM_PROMPT, user_prompt)
    return result
