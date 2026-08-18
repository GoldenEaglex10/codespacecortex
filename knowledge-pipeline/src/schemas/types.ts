/**
 * Core types for the Cortex knowledge pipeline.
 *
 * These are the shapes that flow through: Codespace -> Connector ->
 * Chunker -> Embedder -> Vector store -> Tutor's search tool.
 *
 * Keep this file dependency-free (no DB/SDK imports) so it can be
 * shared by fixtures, tests, and real adapters alike.
 */

/** A school / institution. Every row we store must be scoped to one. */
export type TenantId = string;

/** Raw course pulled from Codespace, before chunking. */
export interface Course {
  tenantId: TenantId;
  courseId: string;
  title: string;
  description?: string;
  lessons: Lesson[];
}

/** A single lesson within a course. */
export interface Lesson {
  lessonId: string;
  courseId: string;
  title: string;
  /** Raw lesson body — markdown or plain text, as Codespace stores it. */
  content: string;
  /** Optional ordering within the course (1-indexed). */
  order?: number;
}

/**
 * A student's progress on a lesson. Not embedded/searched directly,
 * but the tutor's context engine may attach this alongside retrieved
 * chunks — included here so the connector's fetch surface is complete.
 */
export interface ProgressRecord {
  tenantId: TenantId;
  studentId: string;
  lessonId: string;
  status: "not_started" | "in_progress" | "completed";
  lastActivityAt: string; // ISO 8601
}

/**
 * A chunk is the unit we actually embed and search over.
 * One lesson produces many chunks.
 */
export interface Chunk {
  chunkId: string;
  tenantId: TenantId;
  courseId: string;
  lessonId: string;
  /** The chunk's own text — what gets embedded. */
  text: string;
  /** Position of this chunk within its source lesson, 0-indexed. */
  position: number;
  /** Free-form metadata useful for filtering/debugging retrieval. */
  metadata?: {
    heading?: string;
    tokenCount?: number;
    [key: string]: unknown;
  };
}

/** A chunk plus its embedding vector — what actually gets stored. */
export interface EmbeddedChunk extends Chunk {
  embedding: number[];
}

/** Result shape returned by the tenant-scoped search/retrieval tool. */
export interface RetrievedChunk extends Chunk {
  /** Similarity score, higher = more relevant. Meaning depends on metric used. */
  score: number;
}
