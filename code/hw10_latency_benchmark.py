import asyncio
import json
import os
import time
import uuid
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")
PREFIX = os.getenv("PREFIX", "s9004")
INBOX = f"{PREFIX}_inbox"
TOPICS = [f"{PREFIX}_tasks", f"{PREFIX}_drafts", f"{PREFIX}_final"]
OUT = Path("reports/hw10/raw/latency_benchmark.json")
COUNT = 50


def percentile(values, number):
    ordered = sorted(values)
    index = (len(ordered) - 1) * number / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


async def main():
    suffix = uuid.uuid4().hex[:8]
    consumers = [
        AIOKafkaConsumer(
            topic,
            bootstrap_servers=BOOTSTRAP,
            group_id=f"{PREFIX}-hw10-latency-{suffix}-{i}",
            auto_offset_reset="latest",
            enable_auto_commit=False,
        )
        for i, topic in enumerate(TOPICS)
    ]
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    rows = []

    for consumer in consumers:
        await consumer.start()
    await producer.start()

    try:
        for number in range(1, COUNT + 1):
            trace_id = str(uuid.uuid4())
            message = {
                "task_id": str(uuid.uuid4()),
                "correlation_id": trace_id,
                "question": (
                    f"How does Kafka coordinate independent agents? "
                    f"Benchmark request {number}"
                ),
            }
            started = time.perf_counter()
            await producer.send_and_wait(INBOX, json.dumps(message).encode())
            sent = time.perf_counter()
            stage_times = []
            seen = set()
            deadline = time.monotonic() + 45

            while len(seen) < 3 and time.monotonic() < deadline:
                for index, consumer in enumerate(consumers):
                    records = await consumer.getmany(timeout_ms=250, max_records=100)
                    for topic_records in records.values():
                        for record in topic_records:
                            try:
                                item = json.loads(record.value.decode())
                            except (UnicodeDecodeError, json.JSONDecodeError):
                                continue
                            if item.get("correlation_id") != trace_id:
                                continue
                            if index not in seen:
                                seen.add(index)
                                stage_times.append(
                                    {
                                        "stage": ["planner", "writer", "reviewer"][
                                            index
                                        ],
                                        "duration_ms": (time.perf_counter() - sent)
                                        * 1000,
                                    }
                                )
                            break

            if len(seen) != 3:
                raise TimeoutError(f"Trace {trace_id} did not complete all stages")

            row = {
                "request_number": number,
                "trace_id": trace_id,
                "cache_status": "miss",
                "queue_wait_ms": (sent - started) * 1000,
                "stages": {item["stage"]: item["duration_ms"] for item in stage_times},
            }
            row["total_latency_ms"] = max(row["stages"].values()) + row["queue_wait_ms"]
            rows.append(row)
            print(f"miss {number}/{COUNT} trace_id={trace_id}")
    finally:
        await producer.stop()
        for consumer in consumers:
            await consumer.stop()

    metrics = {}
    for stage in ["planner", "writer", "reviewer"]:
        values = [row["stages"][stage] for row in rows]
        metrics[stage] = {
            "p50_ms": percentile(values, 50),
            "p95_ms": percentile(values, 95),
        }
    for name, values in {
        "queue_wait": [row["queue_wait_ms"] for row in rows],
        "total": [row["total_latency_ms"] for row in rows],
    }.items():
        metrics[name] = {
            "p50_ms": percentile(values, 50),
            "p95_ms": percentile(values, 95),
        }

    p95_contributors = {
        stage: metrics[stage]["p95_ms"]
        for stage in ["queue_wait", "planner", "writer", "reviewer"]
    }
    dominant = max(p95_contributors, key=p95_contributors.get)
    output = {
        "cache_miss_count": len(rows),
        "confirmed_cache_miss_count": sum(
            row["cache_status"] == "miss" for row in rows
        ),
        "metrics": metrics,
        "p95_dominant_contributor": dominant,
        "p95_contributor_percent": (
            p95_contributors[dominant] / metrics["total"]["p95_ms"] * 100
        ),
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {key: value for key, value in output.items() if key != "rows"}, indent=2
        )
    )
    print(f"Saved latency benchmark to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
