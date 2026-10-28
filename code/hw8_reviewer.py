import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)

DRAFTS_TOPIC = "s9004_drafts"
FINAL_TOPIC = "s9004_final"


def review_draft(draft):
    return {
        "status": "approved",
        "answer": draft,
        "review": (
            "The draft is clear, relevant, and follows the "
            "planner's requested structure."
        ),
    }


async def main():
    consumer = AIOKafkaConsumer(
        DRAFTS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="s9004-reviewer",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    print(
        f"[REVIEWER] Listening on {DRAFTS_TOPIC}",
        flush=True,
    )

    try:
        async for record in consumer:
            message = json.loads(
                record.value.decode("utf-8"),
            )

            task_id = message["task_id"]
            correlation_id = message["correlation_id"]
            draft = message["draft"]

            print(
                f"[REVIEWER] Received task_id={task_id} "
                f"correlation_id={correlation_id}",
                flush=True,
            )

            review = review_draft(draft)

            output = {
                "task_id": task_id,
                "correlation_id": correlation_id,
                "status": review["status"],
                "answer": review["answer"],
                "review": review["review"],
                "from_agent": "reviewer",
            }

            await producer.send_and_wait(
                FINAL_TOPIC,
                json.dumps(output).encode("utf-8"),
            )

            await consumer.commit()

            print(
                f"[REVIEWER] Sent final result to {FINAL_TOPIC} task_id={task_id}",
                flush=True,
            )

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
