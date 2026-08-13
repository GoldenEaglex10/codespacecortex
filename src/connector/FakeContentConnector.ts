import { ContentConnector } from "./ContentConnector";
import { Course, ProgressRecord, TenantId } from "../schemas/types";
import { sampleCourses } from "../fixtures/sampleCourses";

/**
 * In-memory connector backed by the fake fixtures. Use this for all
 * local development and unit tests until CodespaceRestConnector
 * exists and Jayden's storage is ready to receive real content.
 */
export class FakeContentConnector implements ContentConnector {
  async fetchCourses(tenantId: TenantId): Promise<Course[]> {
    return sampleCourses.filter((c) => c.tenantId === tenantId);
  }

  async fetchCourse(tenantId: TenantId, courseId: string): Promise<Course | null> {
    const course = sampleCourses.find(
      (c) => c.tenantId === tenantId && c.courseId === courseId
    );
    return course ?? null;
  }

  async fetchProgress(
    tenantId: TenantId,
    studentId: string,
    courseId: string
  ): Promise<ProgressRecord[]> {
    // No real progress data in fixtures yet — return an empty set.
    // Kept as a real async method (not a stub throwing) so callers
    // can be written against the final shape now.
    void tenantId;
    void studentId;
    void courseId;
    return [];
  }
}
