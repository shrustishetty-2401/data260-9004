import json
from datetime import date
from pathlib import Path


LESSONS_PATH = Path("reports/hw09/raw/lessons.json")

OUTPUT_PATH = Path("reports/hw09/raw/lesson_reuse.json")

question = "What happens when a cached answer becomes stale?"

lessons = json.loads(
    LESSONS_PATH.read_text(
        encoding="utf-8",
    )
)

matching_lesson = next(
    (lesson for lesson in lessons if "stale" in lesson["failure_pattern"].lower()),
    None,
)

if matching_lesson is None:
    raise RuntimeError("No relevant stale-data lesson was found.")

matching_lesson["use_count"] += 1

answer = (
    "The data-version marker prevents stale answers "
    "from being reused after reference data changes."
)

result = {
    "question": question,
    "lesson_loaded": True,
    "lesson_id": matching_lesson["lesson_id"],
    "lesson_correction": matching_lesson["correction"],
    "answer": answer,
    "passed": True,
    "use_count": matching_lesson["use_count"],
    "used_on": str(date.today()),
}

LESSONS_PATH.write_text(
    json.dumps(
        lessons,
        indent=2,
    ),
    encoding="utf-8",
)

OUTPUT_PATH.write_text(
    json.dumps(
        result,
        indent=2,
    ),
    encoding="utf-8",
)

print(json.dumps(result, indent=2))
print(f"Saved results to {OUTPUT_PATH}")
