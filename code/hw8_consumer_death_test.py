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
DRAFTS_TOPIC = "s9004_drafts"

OUTPUT_PATH = Path(
    "reports/hw08/raw/consumer_death.json",
)


async def main():
    task_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())

    message = {
        "task_id": task_id,
        "correlation_id": correlation_id,
        "question": "Consumer restart recovery test",
        "plan": ("The Writer should recover this task after a mid-processing restart."),
        "delay_seconds": 20,
    }

    consumer = AIOKafkaConsumer(
        DRAFTS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=f"s9004-death-test-{uuid.uuid4()}",
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    try:
        await consumer.getmany(timeout_ms=1000)

        print(
            f"[DEATH TEST] Send task_id={task_id}",
            flush=True,
        )
        print(
            "[DEATH TEST] Kill the Writer while it shows "
            "'Simulating work for 20 seconds'.",
            flush=True,
        )
        print(
            "[DEATH TEST] Then restart the Writer with the same command.",
            flush=True,
        )

        await producer.send_and_wait(
            TASKS_TOPIC,
            json.dumps(message).encode("utf-8"),
        )

        deadline = time.monotonic() + 90

        while time.monotonic() < deadline:
            try:
                record = await asyncio.wait_for(
                    consumer.getone(),
                    timeout=2,
                )
            except asyncio.TimeoutError:
                continue

            result_message = json.loads(
                record.value.decode("utf-8"),
            )

            if result_message.get("task_id") != task_id:
                continue

            result = {
                "task_id": task_id,
                "correlation_id": correlation_id,
                "recovered_after_restart": True,
                "draft_received": True,
                "result": result_message,
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

        raise TimeoutError("No recovered draft received within 90 seconds.")

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
