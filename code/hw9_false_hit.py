import json
from pathlib import Path


INPUT_PATH = Path("reports/hw09/raw/threshold_sweep.json")

OUTPUT_PATH = Path("reports/hw09/raw/false_hit_example.json")

data = json.loads(
    INPUT_PATH.read_text(
        encoding="utf-8",
    )
)

selected_result = next(
    result for result in data["results"] if result["threshold"] == 0.85
)

false_hits = [case for case in selected_result["cases"] if case["false_hit"]]

output = {
    "threshold": selected_result["threshold"],
    "false_hit_count": len(false_hits),
    "false_hits": false_hits,
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
