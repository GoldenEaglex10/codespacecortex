"""
Sample course content used for development and testing, in place of
a live content source. Two distinct tenants are included so tenant
isolation can be verified as part of standard test coverage.
"""

from schemas.models import RawContentItem, ContentType

FAKE_COURSE_DATA: list[RawContentItem] = [
    # ---- Tenant: harare-high-01 ----
    RawContentItem(
        tenant_id="harare-high-01",
        course_id="cs101",
        course_name="Introduction to Programming",
        lesson_id="cs101-l04",
        lesson_title="Loops",
        content_type=ContentType.LESSON,
        text=(
            "A loop lets you repeat a block of code multiple times without "
            "writing it out again and again. In Python, the two main types "
            "are 'for' loops and 'while' loops. A 'for' loop is used when "
            "you know how many times you want to repeat something, such as "
            "iterating over a list of items. A 'while' loop is used when you "
            "want to keep repeating something until a condition becomes "
            "false, such as waiting for user input to be valid. Be careful "
            "with 'while' loops: if the condition never becomes false, you "
            "get an infinite loop, which will freeze your program."
        ),
        source_url="https://codespace.example.com/courses/cs101/lessons/4",
    ),
    RawContentItem(
        tenant_id="harare-high-01",
        course_id="cs101",
        course_name="Introduction to Programming",
        lesson_id="cs101-l05",
        lesson_title="Functions",
        content_type=ContentType.LESSON,
        text=(
            "A function is a reusable block of code that performs a specific "
            "task. Functions help you avoid repeating yourself and make your "
            "code easier to read and test. In Python, you define a function "
            "using the 'def' keyword, followed by a name and parentheses. "
            "Functions can take inputs, called parameters, and can return a "
            "value using the 'return' keyword. Good function names describe "
            "what the function does, like calculate_total or is_valid_email."
        ),
        source_url="https://codespace.example.com/courses/cs101/lessons/5",
    ),
    RawContentItem(
        tenant_id="harare-high-01",
        course_id="cs101",
        course_name="Introduction to Programming",
        lesson_id="cs101-l04-notes",
        lesson_title="Loops — Teacher Notes",
        content_type=ContentType.LESSON_NOTE,
        text=(
            "Common student mistake: forgetting to update the loop variable "
            "inside a 'while' loop, causing an infinite loop. Emphasize "
            "tracing through a loop by hand on the whiteboard before writing "
            "code. Assignment 3 requires students to write a 'for' loop that "
            "sums numbers from 1 to N without using the built-in sum()."
        ),
        source_url=None,
    ),

    # ---- Tenant: bulawayo-college-02 (distinct tenant) ----
    RawContentItem(
        tenant_id="bulawayo-college-02",
        course_id="bio201",
        course_name="Cell Biology",
        lesson_id="bio201-l02",
        lesson_title="Mitosis",
        content_type=ContentType.LESSON,
        text=(
            "Mitosis is the process by which a single cell divides to "
            "produce two genetically identical daughter cells. It consists "
            "of several phases: prophase, metaphase, anaphase, and "
            "telophase. During prophase, chromosomes condense and become "
            "visible. During metaphase, chromosomes align at the cell's "
            "equator. During anaphase, sister chromatids are pulled apart "
            "to opposite poles. During telophase, the nuclear membrane "
            "reforms around each set of chromosomes."
        ),
        source_url="https://codespace.example.com/courses/bio201/lessons/2",
    ),
    RawContentItem(
        tenant_id="bulawayo-college-02",
        course_id="bio201",
        course_name="Cell Biology",
        lesson_id="bio201-l03",
        lesson_title="Photosynthesis",
        content_type=ContentType.LESSON,
        text=(
            "Photosynthesis is the process plants use to convert light "
            "energy into chemical energy stored in glucose. It takes place "
            "mainly in the chloroplasts, using chlorophyll to absorb "
            "sunlight. The overall reaction combines carbon dioxide and "
            "water, using light energy, to produce glucose and oxygen. "
            "Photosynthesis occurs in two main stages: the light-dependent "
            "reactions and the light-independent reactions (Calvin cycle)."
        ),
        source_url="https://codespace.example.com/courses/bio201/lessons/3",
    ),
]
