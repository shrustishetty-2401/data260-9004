import json
import os
import statistics

from retry_demo import simulate_rate


RATES = [0.0, 0.2, 0.5]
RUNS_PER_RATE = 50
VERIFY_SEED = 269004


def percentile(values, percentile):
    ordered = sorted(values)

    if not ordered:
        return 0.0

    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered))
    fraction = position - lower

    return round(
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * fraction,
        3,
    )


def total_elapsed_ms(result):
    return round(
        sum(
            attempt["elapsed_ms"]
            for attempt in result["attempts"]
        ),
        3,
    )


def summarize(rate, records):
    success_count = sum(
        1
        for record in records
        if record["result"]["ok"]
    )

    attempts = [
        record["result"]["total_attempts"]
        for record in records
    ]

    elapsed = [
        total_elapsed_ms(record["result"])
        for record in records
    ]

    return {
        "rate": rate,
        "runs": len(records),
        "successes": success_count,
        "failures": len(records) - success_count,
        "success_rate": round(
            success_count / len(records),
            4,
        ),
        "mean_attempts": round(
            statistics.mean(attempts),
            3,
        ),
        "p99_elapsed_ms": percentile(elapsed, 0.99),
    }


def main():
    output_dir = os.path.expanduser(
        "~/data260-9004/reports/hw05/raw"
    )

    os.makedirs(output_dir, exist_ok=True)

    all_records = []
    summaries = []

    for rate in RATES:
        records = simulate_rate(
            rate=rate,
            total=RUNS_PER_RATE,
            seed=VERIFY_SEED + int(rate * 100),
        )

        for record in records:
            record["scenario"] = "retry_benchmark"
            all_records.append(record)

        summaries.append(summarize(rate, records))

    records_path = os.path.join(
        output_dir,
        "retry_records.jsonl",
    )

    metrics_path = os.path.join(
        output_dir,
        "retry_metrics.json",
    )

    with open(records_path, "w", encoding="utf-8") as file:
        for record in all_records:
            file.write(
                json.dumps(record)
                + "\n"
            )

    with open(metrics_path, "w", encoding="utf-8") as file:
        json.dump(
            {
                "seed": VERIFY_SEED,
                "rates": RATES,
                "runs_per_rate": RUNS_PER_RATE,
                "total_records": len(all_records),
                "summaries": summaries,
            },
            file,
            indent=2,
        )

    print(f"Raw records written: {len(all_records)}")
    print(f"Metrics written: {len(summaries)} groups")


if __name__ == "__main__":
    main()