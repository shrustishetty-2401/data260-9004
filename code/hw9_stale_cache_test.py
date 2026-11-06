import json
import os
from pathlib import Path

from hw9_semantic_cache import SemanticResponseCache


REDIS_URL = os.getenv(
    "SEMANTIC_REDIS_URL",
    "redis://localhost:6381/0",
)

OUTPUT_PATH = Path(
    "reports/hw09/raw/stale_cache.json",
)

QUERY = "What package contains vulnerability HW9-001?"


def old_answer(query: str) -> str:
    return (
        "Vulnerability HW9-001 belongs to package-0 "
        "and is categorized as Input Validation."
    )


def updated_answer(query: str) -> str:
    return (
        "Vulnerability HW9-001 belongs to package-1 "
        "and is categorized as Dependency Risk."
    )


cache = SemanticResponseCache(
    threshold=0.85,
    redis_url=REDIS_URL,
)

cache.invalidate_version("v1")
cache.invalidate_version("v2")

initial_result = cache.get_or_compute(
    query=QUERY,
    answer_function=old_answer,
    data_version="v1",
)

stale_result = cache.get_or_compute(
    query=QUERY,
    answer_function=updated_answer,
    data_version="v1",
)

invalidated_count = cache.invalidate_version("v1")

fresh_result = cache.get_or_compute(
    query=QUERY,
    answer_function=updated_answer,
    data_version="v2",
)

result = {
    "query": QUERY,
    "initial_version": "v1",
    "updated_version": "v2",
    "initial_result": initial_result,
    "stale_result_before_invalidation": stale_result,
    "invalidated_entries": invalidated_count,
    "fresh_result_after_invalidation": fresh_result,
    "stale_answer_was_returned": (stale_result["answer"] == initial_result["answer"]),
    "fresh_answer_was_returned": (fresh_result["answer"] == updated_answer(QUERY)),
}

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_PATH.write_text(
    json.dumps(result, indent=2),
    encoding="utf-8",
)

print(json.dumps(result, indent=2))
print(f"Saved results to {OUTPUT_PATH}")
