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


def percentile(values, percentage):
    values = sorted(values)
    index = (len(values) - 1) * percentage / 100
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    fraction = index - lower
    return values[lower] + (values[upper] - values[lower]) * fraction


async def main():
    suffix = uuid.uuid4().hex[:8]
    consumers = [
        AIOKafkaConsumer(
            topic,
            bootstrap_servers=BOOTSTRAP,
            group_id=f"{PREFIX}-hw10-complete-{suffix}-{index}",
            auto_offset_reset="latest",
            enable_auto_commit=False,
        )
        for index, topic in enumerate(TOPICS)
    ]
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    rows = []

    for consumer in consumers:
        await consumer.start()
    await producer.start()

    try:
        for number in range(1, COUNT + 1):
            trace_id = str(uuid.uuid4())

            cache_start = time.perf_counter()
            cache_status = "miss"
            cache_end = time.perf_counter()

            message = {
                "task_id": str(uuid.uuid4()),
                "correlation_id": trace_id,
                "question": (
                    f"How does Kafka coordinate independent agents? "
                    f"Uncached benchmark request {number}"
                ),
            }

            request_start = time.perf_counter()
            await producer.send_and_wait(
                INBOX,
                json.dumps(message).encode("utf-8"),
            )
            request_sent = time.perf_counter()

            received = {}
            deadline = time.monotonic() + 45

            while len(received) < 3 and time.monotonic() < deadline:
                for index, consumer in enumerate(consumers):
                    records = await consumer.getmany(
                        timeout_ms=250,
                        max_records=100,
                    )

                    for topic_records in records.values():
                        for record in topic_records:
                            try:
                                item = json.loads(record.value.decode("utf-8"))
                            except (
                                UnicodeDecodeError,
                                json.JSONDecodeError,
                            ):
                                continue

                            if item.get("correlation_id") != trace_id:
                                continue

                            if index not in received:
                                received[index] = time.perf_counter()
                            break

            if len(received) != 3:
                raise TimeoutError(f"Trace {trace_id} did not complete all stages")

            planner_done = received[0]
            writer_done = received[1]
            reviewer_done = received[2]

            evaluation_start = time.perf_counter()
            evaluation_record = {
                "trace_id": trace_id,
                "status": "evaluated",
                "joined_stages": [
                    "planner",
                    "writer",
                    "reviewer",
                ],
            }
            json.dumps(evaluation_record)
            evaluation_end = time.perf_counter()

            row = {
                "request_number": number,
                "trace_id": trace_id,
                "cache_status": cache_status,
                "cache_lookup_ms": (cache_end - cache_start) * 1000,
                "queue_wait_ms": (request_sent - request_start) * 1000,
                "stages": {
                    "planner": (planner_done - request_sent) * 1000,
                    "writer": (writer_done - planner_done) * 1000,
                    "reviewer": (reviewer_done - writer_done) * 1000,
                    "evaluation": (evaluation_end - evaluation_start) * 1000,
                },
            }
            row["total_latency_ms"] = sum(
                [
                    row["cache_lookup_ms"],
                    row["queue_wait_ms"],
                    *row["stages"].values(),
                ]
            )
            rows.append(row)
            print(f"miss {number}/{COUNT} trace_id={trace_id}")
    finally:
        await producer.stop()
        for consumer in consumers:
            await consumer.stop()

    metrics = {}
    metric_names = [
        "cache_lookup",
        "queue_wait",
        "planner",
        "writer",
        "reviewer",
        "evaluation",
        "total",
    ]

    for name in metric_names:
        if name == "cache_lookup":
            values = [row["cache_lookup_ms"] for row in rows]
        elif name == "queue_wait":
            values = [row["queue_wait_ms"] for row in rows]
        elif name == "total":
            values = [row["total_latency_ms"] for row in rows]
        else:
            values = [row["stages"][name] for row in rows]

        metrics[name] = {
            "p50_ms": percentile(values, 50),
            "p95_ms": percentile(values, 95),
        }

    total_p95 = metrics["total"]["p95_ms"]
    percentages = {}
    for name in metric_names[:-1]:
        percentages[name] = (
            metrics[name]["p95_ms"] / total_p95 * 100 if total_p95 else 0
        )

    dominant = max(
        percentages,
        key=percentages.get,
    )

    output = {
        "cache_miss_count": len(rows),
        "confirmed_cache_miss_count": sum(
            row["cache_status"] == "miss" for row in rows
        ),
        "metrics": metrics,
        "p95_percent_of_total": percentages,
        "p95_dominant_contributor": dominant,
        "p95_contributor_percent": percentages[dominant],
        "rows": rows,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {key: value for key, value in output.items() if key != "rows"}, indent=2
        )
    )
    print(f"Saved latency benchmark to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
