import { Course } from "../schemas/types";

/**
 * Fake course data, standing in for Codespace's real content until
 * the REST adapter is wired to a live tenant.
 *
 * Two tenants are included on purpose — always test retrieval logic
 * against at least two schools, so cross-tenant leakage is visible
 * from week one, not discovered in the week 5-6 security test.
 */
export const sampleCourses: Course[] = [
  {
    tenantId: "school-alpha",
    courseId: "cs101",
    title: "Introduction to Programming",
    description: "Foundations of programming using Python.",
    lessons: [
      {
        lessonId: "cs101-l01",
        courseId: "cs101",
        title: "Variables and Data Types",
        order: 1,
        content: `# Variables and Data Types

A variable is a named location in memory that stores a value. In Python,
you don't need to declare a type up front — the type is inferred from
the value you assign.

## Common types

- int: whole numbers, e.g. 42
- float: decimal numbers, e.g. 3.14
- str: text, e.g. "hello"
- bool: True or False

## Assignment

Use the = operator to assign a value to a variable name:

    age = 21
    name = "Nyasha"
    is_student = True

Variable names are case-sensitive and cannot start with a digit.`,
      },
      {
        lessonId: "cs101-l02",
        courseId: "cs101",
        title: "Polymorphism",
        order: 2,
        content: `# Polymorphism

Polymorphism means "many forms." In object-oriented programming, it
lets objects of different classes be treated through a common
interface, as long as they implement the same method.

## Example

Two classes, Dog and Cat, can each define a speak() method. Code that
calls animal.speak() doesn't need to know which class animal actually
is — it just needs to know the method exists.

## Why it matters

Polymorphism lets you write code that works with a family of related
types without a long chain of if/else checks for each concrete type.`,
      },
    ],
  },
  {
    tenantId: "school-beta",
    courseId: "web201",
    title: "Web Development Fundamentals",
    description: "HTML, CSS and JavaScript basics.",
    lessons: [
      {
        lessonId: "web201-l01",
        courseId: "web201",
        title: "The DOM",
        order: 1,
        content: `# The Document Object Model

The DOM is a tree-structured representation of an HTML page that
JavaScript can read and modify. Every element, attribute, and piece of
text is a node in this tree.

## Selecting elements

    document.querySelector(".card")
    document.getElementById("main")

## Modifying content

    el.textContent = "Updated!"
    el.classList.add("active")

Changes to the DOM are reflected immediately in the rendered page.`,
      },
    ],
  },
];

/** Convenience: flat list of every fake lesson across all fake tenants. */
export const allSampleLessons = sampleCourses.flatMap((c) => c.lessons);
