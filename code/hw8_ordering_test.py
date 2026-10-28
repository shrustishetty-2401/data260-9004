import asyncio
import json
import os
import random
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
VERIFY_SEED = 269004

OUTPUT_PATH = Path(
    "reports/hw08/raw/ordering_results.json",
)


async def run_case(case_name, use_key):
    rng = random.Random(
        VERIFY_SEED + (1 if use_key else 0),
    )

    consumer = AIOKafkaConsumer(
        DRAFTS_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=(f"s9004-order-{case_name}-{uuid.uuid4()}"),
        auto_offset_reset="latest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    await consumer.getmany(timeout_ms=1000)

    task_ids = set()
    sent_sequences = list(range(1, 21))

    try:
        for sequence in sent_sequences:
            task_id = f"{case_name}-{sequence:02d}-{rng.getrandbits(64):016x}"

            correlation_id = (
                f"{case_name}-corr-{sequence:02d}-{rng.getrandbits(64):016x}"
            )

            task_ids.add(task_id)

            message = {
                "task_id": task_id,
                "correlation_id": correlation_id,
                "question": (f"{case_name} related entity message {sequence}"),
                "plan": ("Process related messages in sequence."),
                "sequence": sequence,
                "entity_key": "vulnerability-42",
            }

            key = b"vulnerability-42" if use_key else None

            await producer.send_and_wait(
                TASKS_TOPIC,
                json.dumps(message).encode("utf-8"),
                key=key,
            )

        received = []
        deadline = time.monotonic() + 60

        while len(received) < 20 and time.monotonic() < deadline:
            try:
                record = await asyncio.wait_for(
                    consumer.getone(),
                    timeout=2,
                )
            except asyncio.TimeoutError:
                continue

            result = json.loads(
                record.value.decode("utf-8"),
            )

            if result.get("task_id") not in task_ids:
                continue

            received.append(
                {
                    "sequence": result.get(
                        "sequence",
                    ),
                    "entity_key": result.get(
                        "entity_key",
                    ),
                    "input_partition": result.get(
                        "input_partition",
                    ),
                    "input_offset": result.get(
                        "input_offset",
                    ),
                    "task_id": result.get(
                        "task_id",
                    ),
                }
            )

        if len(received) != 20:
            raise TimeoutError(f"{case_name} received {len(received)}/20 messages")

        await consumer.commit()

        partitions = sorted({item["input_partition"] for item in received})

        offsets = [item["input_offset"] for item in received]

        sequences = [item["sequence"] for item in received]

        return {
            "case": case_name,
            "key_used": use_key,
            "seed": (VERIFY_SEED + (1 if use_key else 0)),
            "sent_sequences": sent_sequences,
            "received_sequences": sequences,
            "partitions_seen": partitions,
            "offsets_in_receive_order": offsets,
            "message_count": len(received),
            "same_partition": len(partitions) == 1,
            "offsets_increasing": (offsets == sorted(offsets)),
            "messages": received,
        }

    finally:
        await consumer.stop()
        await producer.stop()


async def main():
    print("[ORDERING] Running unkeyed case")

    unkeyed = await run_case(
        "unkeyed",
        use_key=False,
    )

    print("[ORDERING] Running keyed case")

    keyed = await run_case(
        "keyed",
        use_key=True,
    )

    result = {
        "verify_seed": VERIFY_SEED,
        "message_count_per_case": 20,
        "unkeyed": unkeyed,
        "keyed": keyed,
        "keyed_order_preserved": (
            keyed["same_partition"]
            and keyed["offsets_increasing"]
            and keyed["received_sequences"] == list(range(1, 21))
        ),
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


if __name__ == "__main__":
    asyncio.run(main())
