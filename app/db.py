"""
Database layer.

Uses SQLite for now (zero setup). When Phase 1's Postgres + pgvector
is ready, only this file needs to change - the rest of the app talks
to these functions, not to SQL directly.
"""

import sqlite3
import os
import json
from contextlib import contextmanager

DATABASE_PATH = os.getenv("DATABASE_PATH", "./cortex.db")


def init_db():
    """Create tables if they don't exist yet. Safe to call on every startup."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                assignment_id TEXT NOT NULL,
                submission_text TEXT NOT NULL,
                rubric_json TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Phase 1: course material chunks, used by the Tutor agent's
        # context engine for retrieval. tenant_id keeps institutions
        # isolated - every query below always filters by it.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS course_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                title TEXT NOT NULL,
                chunk_text TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Phase 1: tutor conversation log - doubles as an audit trail
        # and as the data source for a later Analytics agent.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tenant_id TEXT NOT NULL,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                mode TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


@contextmanager
def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def save_grade(tenant_id: str, student_id: str, assignment_id: str,
               submission_text: str, rubric: list, result: dict):
    """Persist a graded submission so teachers/analytics can query it later."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO grades
               (tenant_id, student_id, assignment_id, submission_text, rubric_json, result_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (tenant_id, student_id, assignment_id, submission_text,
             json.dumps(rubric), json.dumps(result))
        )
        conn.commit()


def get_grades_for_student(tenant_id: str, student_id: str):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM grades WHERE tenant_id = ? AND student_id = ? ORDER BY created_at DESC",
            (tenant_id, student_id)
        ).fetchall()
        return [dict(row) for row in rows]


# ---- Course content (used by the Tutor agent's retrieval step) ----

def add_course_content(tenant_id: str, course_id: str, title: str, chunk_text: str):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO course_content (tenant_id, course_id, title, chunk_text)
               VALUES (?, ?, ?, ?)""",
            (tenant_id, course_id, title, chunk_text)
        )
        conn.commit()


def get_course_content(tenant_id: str, course_id: str):
    """Every chunk for a course. Always scoped to tenant_id - this is
    the line that prevents one institution's content leaking into
    another's tutoring answers."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM course_content WHERE tenant_id = ? AND course_id = ?",
            (tenant_id, course_id)
        ).fetchall()
        return [dict(row) for row in rows]


# ---- Conversations (audit trail + future analytics input) ----

def log_conversation(tenant_id: str, student_id: str, course_id: str,
                      question: str, answer: str, mode: str):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO conversations (tenant_id, student_id, course_id, question, answer, mode)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (tenant_id, student_id, course_id, question, answer, mode)
        )
        conn.commit()


def get_conversation_history(tenant_id: str, student_id: str, course_id: str, limit: int = 5):
    """Recent Q&A for this student in this course - gives the tutor agent
    short-term memory of what's already been discussed."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT question, answer FROM conversations
               WHERE tenant_id = ? AND student_id = ? AND course_id = ?
               ORDER BY created_at DESC LIMIT ?""",
            (tenant_id, student_id, course_id, limit)
        ).fetchall()
        return [dict(row) for row in reversed(rows)]
