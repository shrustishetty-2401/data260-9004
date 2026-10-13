import json
from pathlib import Path


files = [
    "experiment_short_term_4.json",
    "experiment_short_term_12.json",
    "experiment_short_term_30.json",
    "experiment_eviction_12.json",
]

for filename in files:
    path = Path("reports/hw06/raw") / filename
    data = json.loads(path.read_text())

    completion_values = [
        item["metrics"]["completion_tokens"]
        for item in data["turns"]
    ]

    mean_completion = (
        sum(completion_values)
        / len(completion_values)
    )

    prompt_cost = (
        30
        * data["mean_prompt_tokens_per_turn"]
        / 1_000_000
        * 10_000
    )

    completion_cost = (
        30
        * mean_completion
        / 1_000_000
        * 5
        * 10_000
    )

    total_cost = prompt_cost + completion_cost

    label = data.get(
        "label",
        "baseline",
    )

    print(
        f"{label} "
        f"N={data['short_term_n']}: "
        f"mean_completion={mean_completion:.2f}, "
        f"cost_10000={total_cost:.2f}"
    )