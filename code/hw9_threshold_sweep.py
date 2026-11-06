import json
import time

import yaml

from hw9_semantic_cache import SemanticResponseCache


THRESHOLDS = [
    0.75,
    0.80,
    0.85,
    0.90,
    0.95,
]


with open(
    "cache_cases.yaml",
    "r",
    encoding="utf-8",
) as file:
    cases = yaml.safe_load(file)


exact_cases = [case for case in cases if case["label"] == "exact_duplicate"]


positive_labels = {
    "exact_duplicate",
    "paraphrase_should_hit",
}


negative_labels = {
    "similar_different_answer",
    "unrelated_should_miss",
}


sweep_results = []


for threshold in THRESHOLDS:
    data_version = f"sweep-{threshold:.2f}"

    cache = SemanticResponseCache(
        threshold=threshold,
    )

    cache.invalidate_version(
        data_version,
    )

    # Prime the cache only with exact-reference questions.
    for case in exact_cases:
        cache.get_or_compute(
            query=case["query"],
            answer_function=lambda query: (f"Reference answer for: {query}"),
            data_version=data_version,
        )

    # Allow Redis Stack to index the seeded vectors.
    time.sleep(1)

    results = []

    for case in cases:
        started = time.perf_counter()

        vector = cache.embed(
            case["query"],
        )

        match = cache._search(
            vector,
            data_version,
        )

        latency_ms = (time.perf_counter() - started) * 1000

        similarity = match["similarity"] if match is not None else None

        actual_hit = similarity is not None and similarity >= threshold

        expected_hit = case["label"] in positive_labels

        false_hit = case["label"] in negative_labels and actual_hit

        results.append(
            {
                "case_id": case["case_id"],
                "label": case["label"],
                "query": case["query"],
                "expected_hit": expected_hit,
                "actual_hit": actual_hit,
                "false_hit": false_hit,
                "similarity": similarity,
                "latency_ms": latency_ms,
                "data_version": data_version,
            }
        )

    actual_hits = [row for row in results if row["actual_hit"]]

    true_hits = [row for row in results if row["expected_hit"] and row["actual_hit"]]

    false_hits = [row for row in results if row["false_hit"]]

    negative_case_count = sum(1 for row in results if row["label"] in negative_labels)

    summary = {
        "threshold": threshold,
        "total_cases": len(results),
        "cache_hits": len(actual_hits),
        "hit_rate": (len(actual_hits) / len(results)),
        "true_positive_hits": len(true_hits),
        "false_hits": len(false_hits),
        "false_hit_rate": (
            len(false_hits) / negative_case_count if negative_case_count else 0.0
        ),
        "mean_latency_ms": (sum(row["latency_ms"] for row in results) / len(results)),
        "cases": results,
    }

    sweep_results.append(summary)

    print(
        f"threshold={threshold:.2f} "
        f"hit_rate={summary['hit_rate']:.3f} "
        f"false_hit_rate="
        f"{summary['false_hit_rate']:.3f} "
        f"mean_latency_ms="
        f"{summary['mean_latency_ms']:.2f}",
        flush=True,
    )


output = {
    "thresholds": THRESHOLDS,
    "case_count": len(cases),
    "results": sweep_results,
}


with open(
    "reports/hw09/raw/threshold_sweep.json",
    "w",
    encoding="utf-8",
) as file:
    json.dump(
        output,
        file,
        indent=2,
    )


print("Saved results to reports/hw09/raw/threshold_sweep.json")
