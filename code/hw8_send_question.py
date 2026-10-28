import asyncio
import json
import os
import uuid
from pathlib import Path

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)

INBOX_TOPIC = "s9004_inbox"
FINAL_TOPIC = "s9004_final"
OUTPUT_PATH = Path(
    "reports/hw08/raw/part2_pipeline_result.json",
)


async def main():
    task_id = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())

    question = "How does Kafka improve coordination between independent agents?"

    consumer = AIOKafkaConsumer(
        FINAL_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=f"s9004-sender-{uuid.uuid4()}",
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    message = {
        "task_id": task_id,
        "correlation_id": correlation_id,
        "question": question,
    }

    try:
        print(
            f"[SENDER] Sending question to {INBOX_TOPIC}",
            flush=True,
        )
        print(
            f"[SENDER] task_id={task_id}",
            flush=True,
        )
        print(
            f"[SENDER] correlation_id={correlation_id}",
            flush=True,
        )
        print(
            f"[SENDER] message={json.dumps(message)}",
            flush=True,
        )

        await producer.send_and_wait(
            INBOX_TOPIC,
            json.dumps(message).encode("utf-8"),
        )

        print(
            f"[SENDER] Question sent to {INBOX_TOPIC}",
            flush=True,
        )

        async for record in consumer:
            result = json.loads(
                record.value.decode("utf-8"),
            )

            if result.get("correlation_id") != correlation_id:
                continue

            print(
                f"[SENDER] Final result received from {FINAL_TOPIC}",
                flush=True,
            )
            print(
                json.dumps(result, indent=2),
                flush=True,
            )

            OUTPUT_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            OUTPUT_PATH.write_text(
                json.dumps(result, indent=2),
                encoding="utf-8",
            )

            await consumer.commit()

            print(
                f"Saved result to {OUTPUT_PATH}",
                flush=True,
            )
            return

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
