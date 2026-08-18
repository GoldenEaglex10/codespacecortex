import { ContentConnector } from "./ContentConnector";
import { Course, ProgressRecord, TenantId } from "../schemas/types";

export interface CodespaceRestConnectorConfig {
  /** Base URL of the Codespace API, e.g. https://api.codespace.example.com */
  baseUrl: string;
  /** Service-to-service auth token for calling Codespace on Cortex's behalf. */
  apiToken: string;
}

/**
 * Real adapter — talks to Codespace's actual REST API.
 * TODO: fill in real endpoints once confirmed with the Codespace team.
 * Keep the FakeContentConnector usable in parallel; swap only where
 * the ingestion script wires up its connector, not everywhere it's used.
 */
export class CodespaceRestConnector implements ContentConnector {
  constructor(private config: CodespaceRestConnectorConfig) {}

  async fetchCourses(tenantId: TenantId): Promise<Course[]> {
    const res = await this.get(`/tenants/${tenantId}/courses`);
    // TODO: confirm real response shape and map it onto our Course type
    // rather than assuming it matches 1:1.
    return res as Course[];
  }

  async fetchCourse(tenantId: TenantId, courseId: string): Promise<Course | null> {
    try {
      const res = await this.get(`/tenants/${tenantId}/courses/${courseId}`);
      return res as Course;
    } catch (err) {
      if (this.isNotFound(err)) return null;
      throw err;
    }
  }

  async fetchProgress(
    tenantId: TenantId,
    studentId: string,
    courseId: string
  ): Promise<ProgressRecord[]> {
    const res = await this.get(
      `/tenants/${tenantId}/students/${studentId}/courses/${courseId}/progress`
    );
    return res as ProgressRecord[];
  }

  private async get(path: string): Promise<unknown> {
    const res = await fetch(`${this.config.baseUrl}${path}`, {
      headers: { Authorization: `Bearer ${this.config.apiToken}` },
    });
    if (!res.ok) {
      const err = new Error(`Codespace API ${res.status}: ${path}`) as Error & {
        status?: number;
      };
      err.status = res.status;
      throw err;
    }
    return res.json();
  }

  private isNotFound(err: unknown): boolean {
    return (err as { status?: number })?.status === 404;
  }
}
