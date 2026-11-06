import json
import os

from hw9_semantic_cache import SemanticResponseCache


DATA_VERSION = "v1"


def answer_function(query: str) -> str:
    normalized_query = query.lower()

    if "hw9-001" in normalized_query and (
        "package" in normalized_query or "associated" in normalized_query
    ):
        return (
            "Vulnerability HW9-001 belongs to package-0 "
            "and is categorized as Input Validation."
        )

    return "No matching vulnerability fact was found in the reference data."


cache = SemanticResponseCache(
    threshold=0.85,
    redis_url=os.getenv(
        "SEMANTIC_REDIS_URL",
        "redis://localhost:6381/0",
    ),
)

cache.invalidate_version(DATA_VERSION)

queries = [
    "What package contains vulnerability HW9-001?",
    "What package contains vulnerability HW9-001?",
    "Which package is vulnerability HW9-001 associated with?",
    "What is the unrelated weather forecast today?",
]

results = []

for number, query in enumerate(queries, start=1):
    result = cache.get_or_compute(
        query=query,
        answer_function=answer_function,
        data_version=DATA_VERSION,
    )

    output = {
        "query_number": number,
        "query": query,
        **result,
    }

    results.append(output)

    print(
        json.dumps(
            output,
            indent=2,
        ),
        flush=True,
    )

cached_count = sum(1 for result in results if result["is_cached"])

uncached_count = len(results) - cached_count

summary = {
    "query_count": len(results),
    "cached_count": cached_count,
    "uncached_count": uncached_count,
    "cache_hit_rate": cached_count / len(results),
    "results": results,
}

print(
    json.dumps(
        summary,
        indent=2,
    ),
    flush=True,
)
