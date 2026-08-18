import { Course, ProgressRecord, TenantId } from "../schemas/types";

/**
 * Anything that can supply course content implements this. Today
 * that's FakeContentConnector (fixtures). Later it's
 * CodespaceRestConnector, hitting the real API. The rest of the
 * pipeline (chunker, embedder, ingestion script) only ever depends
 * on this interface — never on a concrete implementation — so
 * swapping fake -> real data is a one-line change in the ingestion
 * script, not a rewrite.
 */
export interface ContentConnector {
  /** Fetch every course for a tenant, lessons included. */
  fetchCourses(tenantId: TenantId): Promise<Course[]>;

  /** Fetch a single course by id, or null if it doesn't exist for that tenant. */
  fetchCourse(tenantId: TenantId, courseId: string): Promise<Course | null>;

  /** Fetch a student's progress records for a course (used by the tutor's context engine, not by search). */
  fetchProgress(
    tenantId: TenantId,
    studentId: string,
    courseId: string
  ): Promise<ProgressRecord[]>;
}
