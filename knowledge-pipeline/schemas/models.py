"""
Typed schemas for the knowledge pipeline.

Defines the data shape at every stage:
Connector -> Chunker -> Embedder -> Vector Store -> Search

All connector implementations (fixture-based or production) return
data conforming to these models, which decouples pipeline stages from
one another and allows implementations to be swapped independently.
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class ContentType(str, Enum):
    LESSON = "lesson"
    LESSON_NOTE = "lesson_note"
    ASSIGNMENT = "assignment"
    COURSE_OVERVIEW = "course_overview"


class RawContentItem(BaseModel):
    """
    A single piece of content as returned by a connector, prior to
    chunking. tenant_id is required on every instance: content is
    tagged with its owning institution from the point it enters the
    pipeline, with no path for untagged content to exist.
    """
    tenant_id: str = Field(..., description="Institution identifier — the tenant isolation key")
    course_id: str
    course_name: str
    lesson_id: str
    lesson_title: str
    content_type: ContentType
    text: str = Field(..., description="Raw text content (lesson body, notes, etc.)")
    source_url: str | None = Field(None, description="Link back to the source content, if available")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Chunk(BaseModel):
    """
    A single searchable piece produced by the chunker from a RawContentItem.
    This is what gets embedded and stored.
    """
    chunk_id: str = Field(..., description="Stable, unique id, e.g. f'{lesson_id}::{index}'")
    tenant_id: str
    course_id: str
    course_name: str
    lesson_id: str
    lesson_title: str
    content_type: ContentType
    chunk_index: int
    text: str
    char_count: int
    source_url: str | None = None


class EmbeddedChunk(Chunk):
    """A Chunk plus its vector embedding, ready to be stored."""
    embedding: list[float]


class SearchQuery(BaseModel):
    """Request payload for the search endpoint."""
    tenant_id: str = Field(..., description="Required. Must be resolved server-side from the authenticated caller, not accepted from client input.")
    query_text: str
    top_k: int = 5


class SearchResult(BaseModel):
    """A single result returned by search."""
    chunk_id: str
    text: str
    score: float
    lesson_title: str
    course_name: str
    source_url: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    tenant_id: str
    query_text: str
