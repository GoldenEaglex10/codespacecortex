# Chunking Strategy

## Rationale

A full lesson is too large and too topically broad to serve as a
single search result. A query such as "what's a while loop?" should
retrieve a focused passage, not an entire multi-topic lesson.

Chunking splits each piece of source content into smaller,
independently searchable segments.

## Approach: paragraph-first, sentence-fallback, with overlap

1. **Split on paragraph boundaries first.**
   Paragraphs typically correspond to a single idea, so this
   preserves semantic coherence better than a fixed-length cut,
   which risks splitting mid-sentence.

2. **Paragraphs exceeding the size limit are split on sentence
   boundaries** and repacked up to a maximum size (default: 500
   characters, roughly 80–100 words) — large enough to retain
   context, small enough to remain focused.

3. **Fragments below a minimum size are merged into the preceding
   chunk** rather than stored standalone, since very short chunks
   retrieve poorly due to insufficient context.

4. **Adjacent chunks overlap by a small margin (default: 50
   characters).** Each chunk includes the tail of the previous
   chunk, preventing loss of context for content that spans a
   chunk boundary.

## Parameter defaults

500 characters / 50-character overlap are initial defaults, not
fixed values — final tuning depends on evaluation with realistic
queries against a production embedding model.

- 500 characters is sized to hold a complete explanation of a single
  concept while remaining focused enough to serve as a direct answer.
- 50-character overlap is small enough to avoid meaningful storage
  overhead while preserving boundary-spanning context.

## Metadata carried per chunk

Each `Chunk` retains full lineage to its source: `tenant_id`,
`course_id`, `lesson_id`, `content_type`, plus a `chunk_index` and
stable `chunk_id` (`{lesson_id}::{index}`).

This supports two requirements:
- **Tenant isolation** — `tenant_id` is carried through to the vector
  store, so filtering is enforced at the chunk level rather than
  reconstructed downstream.
- **Traceability** — `source_url` allows any result to be traced back
  to its originating lesson, supporting both citation and debugging.

## Known limitations

- The sentence splitter is regex-based and will mis-split on
  abbreviations (e.g. "e.g.", "Dr."). Acceptable for current content;
  a proper sentence tokenizer (e.g. `nltk`, `spaCy`) is worth
  adopting if this becomes a measurable issue.
- Chunk size is measured in characters, not tokens, while embedding
  models and LLMs operate on tokens. Once a production embedding
  model is selected, `max_chars` should be re-tuned against actual
  token counts rather than an assumed characters-per-token ratio.
