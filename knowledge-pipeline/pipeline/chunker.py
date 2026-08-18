"""
Splits RawContentItem text into smaller, searchable Chunks.

Strategy (see CHUNKING.md for full rationale):
1. Split on paragraph boundaries.
2. Paragraphs exceeding max_chars are split on sentence boundaries
   and repacked up to the limit.
3. Chunks carry a small overlap with the preceding chunk's tail to
   preserve context across boundaries.
4. Every chunk inherits tenant_id, course_id, and lesson_id from its
   source RawContentItem.
"""

import re
from schemas.models import RawContentItem, Chunk

DEFAULT_MAX_CHARS = 500
DEFAULT_OVERLAP_CHARS = 50
DEFAULT_MIN_CHARS = 40  # merges tiny fragments rather than storing them as standalone chunks


def _split_into_sentences(text: str) -> list[str]:
    # Splits after '.', '!', '?' followed by whitespace. Does not
    # handle abbreviations (e.g. "e.g.", "Dr.") — acceptable for
    # current content, revisit if this becomes a source of errors.
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s for s in sentences if s]


def _split_into_paragraphs(text: str) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in paragraphs if p.strip()]


def _pack_sentences(sentences: list[str], max_chars: int) -> list[str]:
    """Greedily pack sentences into chunks up to max_chars."""
    packed: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                packed.append(current)
            current = sentence
    if current:
        packed.append(current)
    return packed


def chunk_text(
    text: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    min_chars: int = DEFAULT_MIN_CHARS,
) -> list[str]:
    """Pure text -> list[str] chunking, no metadata attached yet."""
    raw_pieces: list[str] = []

    for paragraph in _split_into_paragraphs(text):
        if len(paragraph) <= max_chars:
            raw_pieces.append(paragraph)
        else:
            sentences = _split_into_sentences(paragraph)
            raw_pieces.extend(_pack_sentences(sentences, max_chars))

    # Merge fragments below min_chars into the preceding chunk rather
    # than storing them standalone — short chunks retrieve poorly.
    merged: list[str] = []
    for piece in raw_pieces:
        if merged and len(piece) < min_chars:
            merged[-1] = f"{merged[-1]} {piece}".strip()
        else:
            merged.append(piece)

    # Prepend the tail of the previous chunk to preserve context
    # across boundaries.
    overlapped: list[str] = []
    for i, piece in enumerate(merged):
        if i == 0 or overlap_chars <= 0:
            overlapped.append(piece)
        else:
            prev_tail = merged[i - 1][-overlap_chars:]
            overlapped.append(f"{prev_tail} {piece}".strip())

    return overlapped


def chunk_content_item(
    item: RawContentItem,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[Chunk]:
    """Chunk a RawContentItem into a list of fully-tagged Chunk objects."""
    pieces = chunk_text(item.text, max_chars=max_chars, overlap_chars=overlap_chars)

    chunks: list[Chunk] = []
    for index, piece in enumerate(pieces):
        chunks.append(
            Chunk(
                chunk_id=f"{item.lesson_id}::{index}",
                tenant_id=item.tenant_id,
                course_id=item.course_id,
                course_name=item.course_name,
                lesson_id=item.lesson_id,
                lesson_title=item.lesson_title,
                content_type=item.content_type,
                chunk_index=index,
                text=piece,
                char_count=len(piece),
                source_url=item.source_url,
            )
        )
    return chunks
