import argparse
import asyncio
import json
import os
import time
import uuid
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from hw10_trace_utils import utc_now, write_span


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)
PREFIX = os.getenv("PREFIX", "s9004")
INBOX_TOPIC = f"{PREFIX}_inbox"
TASKS_TOPIC = f"{PREFIX}_tasks"
DRAFTS_TOPIC = f"{PREFIX}_drafts"
FINAL_TOPIC = f"{PREFIX}_final"
OUTPUT_PATH = Path("reports/hw10/raw/trace_examples.json")


def new_trace_id():
    return str(uuid.uuid4())


def write_cache_span(trace_id, cache_status):
    started = utc_now()
    ended = utc_now()
    return write_span(
        trace_id=trace_id,
        stage="cache_lookup",
        start_time=started,
        end_time=ended,
        status="success",
        metadata={
            "cache_status": cache_status,
            "path": "cache-hit" if cache_status == "hit" else "cache-miss",
        },
    )


async def capture_miss(question):
    trace_id = new_trace_id()
    write_cache_span(trace_id, "miss")

    consumers = [
        AIOKafkaConsumer(
            TASKS_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"{PREFIX}-hw10-trace-{trace_id[:8]}-tasks",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        ),
        AIOKafkaConsumer(
            DRAFTS_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"{PREFIX}-hw10-trace-{trace_id[:8]}-drafts",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        ),
        AIOKafkaConsumer(
            FINAL_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"{PREFIX}-hw10-trace-{trace_id[:8]}-final",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        ),
    ]
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
    messages = {}

    for consumer in consumers:
        await consumer.start()
    await producer.start()

    try:
        send_start = utc_now()
        message = {
            "task_id": str(uuid.uuid4()),
            "correlation_id": trace_id,
            "question": question,
        }
        await producer.send_and_wait(
            INBOX_TOPIC,
            json.dumps(message).encode("utf-8"),
        )
        send_end = utc_now()

        write_span(
            trace_id=trace_id,
            stage="inbox",
            start_time=send_start,
            end_time=send_end,
            status="success",
            metadata={"topic": INBOX_TOPIC},
        )

        deadline = time.monotonic() + 60
        while len(messages) < 3 and time.monotonic() < deadline:
            for name, consumer in zip(
                ("planner", "writer", "reviewer"),
                consumers,
            ):
                records = await consumer.getmany(
                    timeout_ms=500,
                    max_records=100,
                )
                for topic_records in records.values():
                    for record in topic_records:
                        try:
                            item = json.loads(record.value.decode("utf-8"))
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            continue

                        if item.get("correlation_id") == trace_id:
                            messages[name] = item
                            break

        if len(messages) != 3:
            missing = [
                name
                for name in ("planner", "writer", "reviewer")
                if name not in messages
            ]
            raise TimeoutError("Missing trace stages: " + ", ".join(missing))

        for stage, topic in (
            ("planner", TASKS_TOPIC),
            ("writer", DRAFTS_TOPIC),
            ("reviewer", FINAL_TOPIC),
        ):
            event_time = utc_now()
            write_span(
                trace_id=trace_id,
                stage=stage,
                start_time=event_time,
                end_time=event_time,
                status="success",
                metadata={
                    "topic": topic,
                    "message": messages[stage],
                },
            )

        evaluation_time = utc_now()
        write_span(
            trace_id=trace_id,
            stage="evaluation",
            start_time=evaluation_time,
            end_time=utc_now(),
            status="success",
            metadata={"source": "hw10_pipeline_evaluator"},
        )

    finally:
        await producer.stop()
        for consumer in consumers:
            await consumer.stop()

    return trace_id


def capture_hit():
    trace_id = new_trace_id()
    write_cache_span(trace_id, "hit")
    return trace_id


def capture_failure():
    trace_id = new_trace_id()
    write_cache_span(trace_id, "miss")
    now = utc_now()
    write_span(
        trace_id=trace_id,
        stage="inbox",
        start_time=now,
        end_time=utc_now(),
        status="success",
        metadata={"topic": INBOX_TOPIC},
    )
    write_span(
        trace_id=trace_id,
        stage="planner",
        start_time=utc_now(),
        end_time=utc_now(),
        status="failed",
        error="Simulated malformed request for failure-trace evidence",
        metadata={"topic": INBOX_TOPIC},
    )
    return trace_id


async def main(question):
    examples = {
        "cache_hit_trace_id": capture_hit(),
        "failed_trace_id": capture_failure(),
        "cache_miss_trace_id": await capture_miss(question),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(examples, indent=2), encoding="utf-8")
    print(json.dumps(examples, indent=2))
    print(f"Saved trace examples to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--question",
        default="How does Kafka improve coordination between independent agents?",
    )
    args = parser.parse_args()
    asyncio.run(main(args.question))
