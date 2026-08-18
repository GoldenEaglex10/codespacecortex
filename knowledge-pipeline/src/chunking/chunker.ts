import { Chunk, Lesson } from "../schemas/types";

/**
 * CHUNKING STRATEGY — heading-first, size-bounded.
 *
 * Why this approach:
 *
 * 1. Lesson content is markdown-ish and already organized under `#`/`##`
 *    headings written by course authors. Splitting on headings first
 *    keeps each chunk topically coherent — a student question about
 *    "polymorphism" should retrieve the whole polymorphism section,
 *    not half of it glued to half of the variables section.
 *
 * 2. Some sections are still too long to embed/retrieve well (a wall
 *    of text hurts embedding quality and wastes context). So within
 *    each heading section, we further split on a max character budget,
 *    breaking on paragraph boundaries (blank lines) so we never cut a
 *    sentence in half.
 *
 * 3. We do NOT chunk purely by fixed token count with no regard for
 *    structure — that tends to split a code example from the sentence
 *    explaining it, which is exactly the kind of bad retrieval this
 *    pipeline exists to avoid.
 *
 * Tuning: MAX_CHUNK_CHARS is deliberately in characters, not tokens,
 * to avoid a tokenizer dependency here. ~1200 chars is roughly 250-300
 * tokens — small enough for precise retrieval, large enough to keep
 * an explanation and its example together. Adjust based on real
 * search-quality testing (task 7 in the ClickUp checklist).
 */
const MAX_CHUNK_CHARS = 1200;

interface Section {
  heading: string | null;
  body: string;
}

/** Split lesson markdown into sections by heading line (# or ##). */
function splitByHeading(content: string): Section[] {
  const lines = content.split("\n");
  const sections: Section[] = [];
  let currentHeading: string | null = null;
  let currentLines: string[] = [];

  const flush = () => {
    const body = currentLines.join("\n").trim();
    if (body.length > 0) {
      sections.push({ heading: currentHeading, body });
    }
    currentLines = [];
  };

  for (const line of lines) {
    const headingMatch = /^#{1,3}\s+(.*)/.exec(line);
    if (headingMatch) {
      flush();
      currentHeading = headingMatch[1].trim();
    } else {
      currentLines.push(line);
    }
  }
  flush();

  return sections;
}

/** Split a section body further if it exceeds MAX_CHUNK_CHARS, breaking on blank lines. */
function splitBySize(body: string, maxChars: number): string[] {
  if (body.length <= maxChars) return [body];

  const paragraphs = body.split(/\n\s*\n/);
  const parts: string[] = [];
  let current = "";

  for (const para of paragraphs) {
    const candidate = current ? `${current}\n\n${para}` : para;
    if (candidate.length > maxChars && current) {
      parts.push(current);
      current = para;
    } else {
      current = candidate;
    }
  }
  if (current) parts.push(current);

  return parts;
}

/**
 * Turn one lesson into an ordered list of chunks, ready for embedding.
 * chunkId is deterministic (lessonId + position) so re-running ingestion
 * on the same lesson produces stable ids instead of duplicating rows.
 */
export function chunkLesson(lesson: Lesson, tenantId: string): Chunk[] {
  const sections = splitByHeading(lesson.content);
  const chunks: Chunk[] = [];
  let position = 0;

  for (const section of sections) {
    const pieces = splitBySize(section.body, MAX_CHUNK_CHARS);
    for (const text of pieces) {
      chunks.push({
        chunkId: `${lesson.lessonId}-${position}`,
        tenantId,
        courseId: lesson.courseId,
        lessonId: lesson.lessonId,
        text: section.heading ? `${section.heading}\n\n${text}` : text,
        position,
        metadata: {
          heading: section.heading ?? undefined,
          tokenCount: undefined, // fill in once the embedder's tokenizer is wired up
        },
      });
      position += 1;
    }
  }

  return chunks;
}
