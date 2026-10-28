import asyncio
import json
import os
import time
import uuid
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)

TASKS_TOPIC = "s9004_tasks"
DEAD_LETTER_TOPIC = "s9004_dead_letter"

OUTPUT_PATH = Path(
    "reports/hw08/raw/poison_message.json",
)


async def main():
    task_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())

    message = {
        "task_id": task_id,
        "correlation_id": correlation_id,
        "question": "Poison message test",
        "plan": ("This message should fail and go to the dead-letter topic."),
        "poison": True,
    }

    consumer = AIOKafkaConsumer(
        DEAD_LETTER_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=f"s9004-dlq-test-{uuid.uuid4()}",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    try:
        # Force the consumer to join the group before sending.
        await consumer.getmany(timeout_ms=1000)

        print(
            f"[POISON] Sending task_id={task_id}",
            flush=True,
        )

        await producer.send_and_wait(
            TASKS_TOPIC,
            json.dumps(message).encode("utf-8"),
        )

        deadline = time.monotonic() + 30

        while time.monotonic() < deadline:
            try:
                record = await asyncio.wait_for(
                    consumer.getone(),
                    timeout=2,
                )
            except asyncio.TimeoutError:
                continue

            dead_letter = json.loads(
                record.value.decode("utf-8"),
            )

            if dead_letter.get("task_id") != task_id:
                continue

            result = {
                "task_id": task_id,
                "correlation_id": correlation_id,
                "dead_letter_topic": DEAD_LETTER_TOPIC,
                "retry_count": dead_letter.get(
                    "retry_count",
                ),
                "dead_letter_reason": dead_letter.get(
                    "dead_letter_reason",
                ),
                "moved_to_dead_letter": True,
            }

            OUTPUT_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            OUTPUT_PATH.write_text(
                json.dumps(result, indent=2),
                encoding="utf-8",
            )

            print(json.dumps(result, indent=2))
            print(f"Saved results to {OUTPUT_PATH}")

            await consumer.commit()
            return

        raise TimeoutError(
            "No matching dead-letter message received within 30 seconds."
        )

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
