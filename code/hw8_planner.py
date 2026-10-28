import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)

INBOX_TOPIC = "s9004_inbox"
TASKS_TOPIC = "s9004_tasks"


def build_plan(question):
    return (
        f"Plan for the question '{question}': "
        "1. Identify the main goal. "
        "2. Gather the relevant facts. "
        "3. Organize the answer clearly. "
        "4. Ask the Writer to produce a concise response."
    )


async def main():
    consumer = AIOKafkaConsumer(
        INBOX_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="s9004-planner",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    print(
        f"[PLANNER] Listening on {INBOX_TOPIC}",
        flush=True,
    )

    try:
        async for record in consumer:
            message = json.loads(
                record.value.decode("utf-8"),
            )

            task_id = message["task_id"]
            correlation_id = message["correlation_id"]
            question = message["question"]

            print(
                f"[PLANNER] Received task_id={task_id} correlation_id={correlation_id}",
                flush=True,
            )

            plan = build_plan(question)

            output = {
                "task_id": task_id,
                "correlation_id": correlation_id,
                "question": question,
                "plan": plan,
                "from_agent": "planner",
            }

            await producer.send_and_wait(
                TASKS_TOPIC,
                json.dumps(output).encode("utf-8"),
            )

            await consumer.commit()

            print(
                f"[PLANNER] Sent plan to {TASKS_TOPIC} task_id={task_id}",
                flush=True,
            )

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
