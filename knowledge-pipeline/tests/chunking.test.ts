import { FakeContentConnector } from "../src/connector/FakeContentConnector";
import { chunkLesson } from "../src/chunking/chunker";

async function main() {
  const connector = new FakeContentConnector();
  const courses = await connector.fetchCourses("school-alpha");

  console.log(`Fetched ${courses.length} course(s) for school-alpha`);

  for (const course of courses) {
    for (const lesson of course.lessons) {
      const chunks = chunkLesson(lesson, course.tenantId);
      console.log(
        `\n--- ${course.title} / ${lesson.title}: ${chunks.length} chunk(s) ---`
      );
      for (const chunk of chunks) {
        console.log(`[${chunk.chunkId}] (${chunk.text.length} chars)`);
        console.log(chunk.text.slice(0, 80).replace(/\n/g, " ") + "...");
      }
    }
  }

  // Basic sanity checks — not a full test framework yet, just a smoke test.
  const alphaCourses = await connector.fetchCourses("school-alpha");
  const betaCourses = await connector.fetchCourses("school-beta");
  const leaked = alphaCourses.some((c) =>
    betaCourses.some((b) => b.courseId === c.courseId)
  );
  console.log(`\nCross-tenant leak check: ${leaked ? "FAIL" : "PASS"}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
