import json
from statistics import mean

from hw9_semantic_cache import SemanticResponseCache


def answer_function(query: str) -> str:
    normalized = query.lower()

    if "package" in normalized:
        return "Vulnerability HW9-001 belongs to package-0."

    if "category" in normalized:
        return "Vulnerability HW9-001 is in the Input Validation category."

    if "topic" in normalized:
        return "Vulnerability requests use the s9004_vulnerability_requests topic."

    if "redis" in normalized:
        return "Redis stores the cached embedding, answer, and data-version marker."

    return "No matching vulnerability fact was found in the reference data."


cache = SemanticResponseCache(
    threshold=0.85,
)

data_version = "experiment-v1"
cache.invalidate_version(data_version)

queries = [
    "What package contains vulnerability HW9-001?",
    "What package contains vulnerability HW9-001?",
    "Which package is vulnerability HW9-001 associated with?",
    "What category is vulnerability HW9-001 in?",
    "Which category contains vulnerability HW9-001?",
    "Which Kafka topic receives vulnerability requests?",
    "What topic handles vulnerability requests?",
    "What does Redis store for the semantic cache?",
    "What is the weather forecast today?",
    "What is the capital of France?",
]

results = []

for number, query in enumerate(queries, start=1):
    result = cache.get_or_compute(
        query=query,
        answer_function=answer_function,
        data_version=data_version,
    )

    row = {
        "query_number": number,
        "query": query,
        **result,
    }

    results.append(row)

    print(
        json.dumps(
            row,
            indent=2,
        ),
        flush=True,
    )

cached_results = [row for row in results if row["is_cached"] is True]

uncached_results = [row for row in results if row["is_cached"] is False]

summary = {
    "query_count": len(results),
    "cached_count": len(cached_results),
    "uncached_count": len(uncached_results),
    "cache_hit_rate": (len(cached_results) / len(results)),
    "average_cached_latency_ms": (
        mean(row["latency_ms"] for row in cached_results) if cached_results else None
    ),
    "average_uncached_latency_ms": (
        mean(row["latency_ms"] for row in uncached_results)
        if uncached_results
        else None
    ),
}

output = {
    "threshold": 0.85,
    "data_version": data_version,
    "results": results,
    "summary": summary,
}

with open(
    "reports/hw09/raw/part2_cache_10_queries.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        output,
        file,
        indent=2,
    )

print(json.dumps(summary, indent=2))
print("Saved results to reports/hw09/raw/part2_cache_10_queries.json")
