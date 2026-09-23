import csv
import json
import statistics
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import (
    HTTPCookieProcessor,
    Request,
    build_opener,
)

BASE_URL = "http://localhost:8004"
EMAIL = "student@example.com"
PASSWORD = "data260"

PAGE_SIZES = [10, 50, 200]
MODES = ["naive", "fixed"]
REQUESTS_PER_GROUP = 30

OUTPUT_DIR = Path("reports/hw04/raw")
JSON_OUTPUT = OUTPUT_DIR / "n_plus_one_requests.json"
CSV_OUTPUT = OUTPUT_DIR / "n_plus_one_requests.csv"
METRICS_OUTPUT = OUTPUT_DIR / "n_plus_one_metrics.json"


def percentile(values: list[float], percentage: float) -> float:
    ordered = sorted(values)

    if not ordered:
        return 0.0

    position = (len(ordered) - 1) * percentage
    lower = int(position)
    upper = min(lower + 1, len(ordered))
    fraction = position - lower

    return ordered[lower] + (
        ordered[upper] - ordered[lower]
    ) * fraction


def request_json(opener, method, url, payload=None):
    body = None
    headers = {}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )

    with opener.open(request) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    opener = build_opener(
        HTTPCookieProcessor()
    )

    login_result = request_json(
        opener,
        "POST",
        f"{BASE_URL}/api/auth/login",
        {
            "email": EMAIL,
            "password": PASSWORD,
        },
    )

    print(f"Logged in as: {login_result['email']}")

    raw_results = []

    for mode in MODES:
        for page_size in PAGE_SIZES:
            print(
                f"Running mode={mode}, "
                f"page_size={page_size}, "
                f"requests={REQUESTS_PER_GROUP}"
            )

            for repetition in range(1, REQUESTS_PER_GROUP + 1):
                url = (
                    f"{BASE_URL}/api/benchmark/reports/"
                    f"{mode}?page_size={page_size}"
                )

                started = time.perf_counter()

                try:
                    result = request_json(
                        opener,
                        "GET",
                        url,
                    )
                    status = "ok"
                    error = ""

                except HTTPError as request_error:
                    result = {}
                    status = "error"
                    error = str(request_error)

                latency_ms = (
                    time.perf_counter() - started
                ) * 1000

                raw_results.append(
                    {
                        "mode": mode,
                        "page_size": page_size,
                        "repetition": repetition,
                        "latency_ms": round(latency_ms, 3),
                        "sql_statements": result.get(
                            "sql_statements",
                            None,
                        ),
                        "rows_returned": result.get(
                            "rows_returned",
                            None,
                        ),
                        "status": status,
                        "error": error,
                    }
                )

    with JSON_OUTPUT.open("w", encoding="utf-8") as output_file:
        json.dump(
            raw_results,
            output_file,
            indent=2,
        )

    fieldnames = [
        "mode",
        "page_size",
        "repetition",
        "latency_ms",
        "sql_statements",
        "rows_returned",
        "status",
        "error",
    ]

    with CSV_OUTPUT.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(raw_results)

    metrics = []

    for mode in MODES:
        for page_size in PAGE_SIZES:
            group = [
                row
                for row in raw_results
                if row["mode"] == mode
                and row["page_size"] == page_size
                and row["status"] == "ok"
            ]

            latencies = [
                row["latency_ms"]
                for row in group
            ]

            sql_counts = [
                row["sql_statements"]
                for row in group
                if row["sql_statements"] is not None
            ]

            metrics.append(
                {
                    "mode": mode,
                    "page_size": page_size,
                    "requests": len(group),
                    "sql_statements_per_request": (
                        statistics.mean(sql_counts)
                        if sql_counts
                        else None
                    ),
                    "p50_latency_ms": round(
                        percentile(latencies, 0.50),
                        3,
                    ),
                    "p95_latency_ms": round(
                        percentile(latencies, 0.95),
                        3,
                    ),
                    "p99_latency_ms": round(
                        percentile(latencies, 0.99),
                        3,
                    ),
                }
            )

    with METRICS_OUTPUT.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            metrics,
            output_file,
            indent=2,
        )

    print(f"Raw JSON saved to {JSON_OUTPUT}")
    print(f"Raw CSV saved to {CSV_OUTPUT}")
    print(f"Metrics saved to {METRICS_OUTPUT}")
    print(f"Total requests: {len(raw_results)}")


if __name__ == "__main__":
    main()