import json
from pathlib import Path


INPUT_PATH = Path("reports/hw09/raw/threshold_sweep.json")

OUTPUT_PATH = Path("reports/hw09/raw/cost_model.json")

# Relative cost assumptions.
CACHE_HIT_COST = 1.0
CORRECT_MISS_COST = 10.0
FALSE_HIT_PENALTY = 30.0

data = json.loads(
    INPUT_PATH.read_text(
        encoding="utf-8",
    )
)

rows = []

for result in data["results"]:
    cases = result["cases"]

    cache_hits = sum(
        1 for case in cases if case["actual_hit"] and not case["false_hit"]
    )

    correct_misses = sum(1 for case in cases if not case["actual_hit"])

    false_hits = sum(1 for case in cases if case["false_hit"])

    total_cost = (
        cache_hits * CACHE_HIT_COST
        + correct_misses * CORRECT_MISS_COST
        + false_hits * FALSE_HIT_PENALTY
    )

    rows.append(
        {
            "threshold": result["threshold"],
            "hit_rate": result["hit_rate"],
            "false_hit_rate": result["false_hit_rate"],
            "cache_hits": cache_hits,
            "correct_misses": correct_misses,
            "false_hits": false_hits,
            "total_cost": total_cost,
            "cost_per_query": total_cost / result["total_cases"],
        }
    )

recommended = min(
    rows,
    key=lambda row: (
        row["false_hits"] > 0,
        row["total_cost"],
    ),
)

output = {
    "cost_assumptions": {
        "cache_hit_cost": CACHE_HIT_COST,
        "correct_miss_cost": CORRECT_MISS_COST,
        "false_hit_penalty": FALSE_HIT_PENALTY,
    },
    "results": rows,
    "recommended_threshold": recommended["threshold"],
    "recommendation_reason": (
        "Choose the highest-correctness threshold with zero "
        "false hits for vulnerability answers."
    ),
}

OUTPUT_PATH.write_text(
    json.dumps(
        output,
        indent=2,
    ),
    encoding="utf-8",
)

print(json.dumps(output, indent=2))
print(f"Saved results to {OUTPUT_PATH}")
