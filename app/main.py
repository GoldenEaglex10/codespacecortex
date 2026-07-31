"""
Codespace Cortex - Tutor, Assessment, and Content agents

Run with:
    uvicorn app.main:app --reload

Every route (except /health) requires an Authorization header:
    Authorization: Bearer <api_key>

On first run, a default development API key is created automatically and
printed to the console - copy it from there. tenant_id is resolved from
this key, never from anything in the request body, which is what actually
prevents one tenant from reading another's data.
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
import logging

from app.db import (
    init_db, seed_default_api_key_if_missing,
    save_grade, get_grades_for_student,
    add_course_content, log_conversation,
    save_generated_content, get_generated_content,
)
from app.auth import require_tenant
from app.assessment import grade_submission
from app.tutor import ask_tutor
from app.content import generate_quiz

load_dotenv()

logger = logging.getLogger("cortex")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Codespace Cortex")


@app.on_event("startup")
def startup():
    init_db()
    seed_default_api_key_if_missing()


# ---- Global safety net ----
# Catches anything not already handled by a route's own try/except, so
# the caller always gets clean JSON instead of a raw Python traceback.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong processing this request. Check server logs for details."},
    )


# ---- Request/response models ----
# Note: none of these carry a tenant_id field anymore. Tenant identity
# comes from the Authorization header (see app/auth.py), not from
# anything the caller can type into the request body.

class RubricCriterion(BaseModel):
    criterion: str
    max_points: float
    description: str

    @field_validator("criterion", "description")
    @classmethod
    def not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("cannot be blank")
        return v

    @field_validator("max_points")
    @classmethod
    def positive_points(cls, v):
        if v <= 0:
            raise ValueError("max_points must be greater than 0")
        return v


class GradeRequest(BaseModel):
    student_id: str
    assignment_id: str
    submission_text: str
    rubric: list[RubricCriterion]

    @field_validator("submission_text")
    @classmethod
    def submission_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("submission_text cannot be blank")
        return v

    @field_validator("rubric")
    @classmethod
    def rubric_not_empty(cls, v):
        if not v:
            raise ValueError("rubric must have at least one criterion")
        return v


class CourseContentRequest(BaseModel):
    course_id: str
    title: str
    chunk_text: str

    @field_validator("chunk_text")
    @classmethod
    def chunk_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("chunk_text cannot be blank")
        return v


class TutorAskRequest(BaseModel):
    student_id: str
    course_id: str
    question: str
    mode: str = "free_help"  # "free_help" or "graded_work"

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("question cannot be blank")
        return v


class GenerateQuizRequest(BaseModel):
    course_id: str
    topic: str
    num_questions: int = 5
    difficulty: str = "mixed"  # "easy", "medium", "hard", or "mixed"

    @field_validator("topic")
    @classmethod
    def topic_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("topic cannot be blank")
        return v

    @field_validator("num_questions")
    @classmethod
    def reasonable_question_count(cls, v):
        if v < 1 or v > 20:
            raise ValueError("num_questions must be between 1 and 20")
        return v


# ---- Routes ----

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/assessment/grade")
def grade(req: GradeRequest, tenant_id: str = Depends(require_tenant)):
    rubric_dicts = [r.model_dump() for r in req.rubric]

    try:
        result = grade_submission(req.submission_text, rubric_dicts)
    except ValueError as e:
        logger.error(f"Assessment agent returned unparseable output: {e}")
        raise HTTPException(status_code=502, detail="The grading model returned an unusable response. Try again.")
    except RuntimeError as e:
        logger.error(f"Assessment agent config/connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    save_grade(
        tenant_id=tenant_id,
        student_id=req.student_id,
        assignment_id=req.assignment_id,
        submission_text=req.submission_text,
        rubric=rubric_dicts,
        result=result,
    )

    return result


@app.get("/assessment/grades/{student_id}")
def list_grades(student_id: str, tenant_id: str = Depends(require_tenant)):
    return get_grades_for_student(tenant_id, student_id)


# ---- Tutor agent + content ingestion ----

@app.post("/content/ingest")
def ingest_content(req: CourseContentRequest, tenant_id: str = Depends(require_tenant)):
    """
    Loads a chunk of course material for retrieval. In a real system this
    would be triggered by the connector layer syncing from the LMS; for
    now, call this directly to seed course content for testing the tutor.
    """
    add_course_content(tenant_id, req.course_id, req.title, req.chunk_text)
    return {"status": "ingested"}


@app.post("/tutor/ask")
def tutor_ask(req: TutorAskRequest, tenant_id: str = Depends(require_tenant)):
    if req.mode not in ("free_help", "graded_work"):
        raise HTTPException(status_code=400, detail="mode must be 'free_help' or 'graded_work'")

    try:
        answer = ask_tutor(tenant_id, req.student_id, req.course_id, req.question, req.mode)
    except RuntimeError as e:
        logger.error(f"Tutor agent config/connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    log_conversation(tenant_id, req.student_id, req.course_id, req.question, answer, req.mode)

    return {"answer": answer, "mode": req.mode}


# ---- Content agent ----

@app.post("/content/generate-quiz")
def generate_quiz_route(req: GenerateQuizRequest, tenant_id: str = Depends(require_tenant)):
    try:
        result = generate_quiz(
            tenant_id, req.course_id, req.topic,
            req.num_questions, req.difficulty
        )
    except ValueError as e:
        logger.error(f"Content agent returned unparseable output: {e}")
        raise HTTPException(status_code=502, detail="The quiz generation model returned an unusable response. Try again.")
    except RuntimeError as e:
        logger.error(f"Content agent config/connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))

    save_generated_content(tenant_id, req.course_id, "quiz", req.topic, result)
    return result


@app.get("/content/generated/{course_id}")
def list_generated_content(course_id: str, tenant_id: str = Depends(require_tenant)):
    return get_generated_content(tenant_id, course_id)
