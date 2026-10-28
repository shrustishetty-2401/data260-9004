import asyncio
import json
import os
from collections import defaultdict

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)

TASKS_TOPIC = "s9004_tasks"
DRAFTS_TOPIC = "s9004_drafts"
DEAD_LETTER_TOPIC = "s9004_dead_letter"

MAX_RETRIES = 3

attempts = defaultdict(int)
processed_tasks = set()


def build_draft(question, plan):
    return (
        f"Answer draft for '{question}': "
        f"Following the planner's approach, {plan} "
        "The main recommendation is to use a clear, "
        "evidence-based answer that directly addresses "
        "the question."
    )


async def process_message(
    message,
    producer,
    input_partition,
    input_offset,
):
    task_id = message["task_id"]
    correlation_id = message["correlation_id"]

    if task_id in processed_tasks:
        print(
            f"[WRITER] Duplicate task ignored: {task_id}",
            flush=True,
        )
        return

    if message.get("poison") is True:
        raise ValueError(
            "Poison message requested failure",
        )

    delay_seconds = float(
        message.get("delay_seconds", 0),
    )

    if delay_seconds > 0:
        print(
            f"[WRITER] Simulating work for {delay_seconds} seconds",
            flush=True,
        )
        await asyncio.sleep(delay_seconds)

    question = message["question"]
    plan = message["plan"]
    draft = build_draft(question, plan)

    output = {
        "task_id": task_id,
        "correlation_id": correlation_id,
        "question": question,
        "draft": draft,
        "from_agent": "writer",
        "sequence": message.get("sequence"),
        "entity_key": message.get("entity_key"),
        "input_partition": input_partition,
        "input_offset": input_offset,
    }

    await producer.send_and_wait(
        DRAFTS_TOPIC,
        json.dumps(output).encode("utf-8"),
    )

    processed_tasks.add(task_id)

    print(
        f"[WRITER] Draft sent to {DRAFTS_TOPIC} task_id={task_id}",
        flush=True,
    )


async def main():
    consumer = AIOKafkaConsumer(
        TASKS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="s9004-writer",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    print(
        f"[WRITER] Listening on {TASKS_TOPIC}",
        flush=True,
    )

    try:
        async for record in consumer:
            message = json.loads(
                record.value.decode("utf-8"),
            )

            task_id = message.get("task_id")
            attempt_key = (
                record.partition,
                record.offset,
            )

            print(
                f"[WRITER] Received task_id={task_id} "
                f"partition={record.partition} "
                f"offset={record.offset}",
                flush=True,
            )

            print(
                f"[WRITER] sequence={message.get('sequence')} "
                f"entity_key={message.get('entity_key')}",
                flush=True,
            )

            while True:
                try:
                    await process_message(
                        message,
                        producer,
                        record.partition,
                        record.offset,
                    )

                    await consumer.commit()

                    print(
                        f"[WRITER] Offset committed for task_id={task_id}",
                        flush=True,
                    )
                    break

                except Exception as error:
                    attempts[attempt_key] += 1
                    retry_number = attempts[attempt_key]

                    print(
                        f"[WRITER] Processing failed for "
                        f"task_id={task_id}; "
                        f"retry={retry_number}/{MAX_RETRIES}; "
                        f"error={error}",
                        flush=True,
                    )

                    if retry_number >= MAX_RETRIES:
                        dead_letter_message = {
                            **message,
                            "dead_letter_reason": str(
                                error,
                            ),
                            "retry_count": retry_number,
                        }

                        await producer.send_and_wait(
                            DEAD_LETTER_TOPIC,
                            json.dumps(
                                dead_letter_message,
                            ).encode("utf-8"),
                        )

                        await consumer.commit()

                        print(
                            f"[WRITER] Sent task_id={task_id} to {DEAD_LETTER_TOPIC}",
                            flush=True,
                        )
                        break

                    await asyncio.sleep(1)

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(main())
