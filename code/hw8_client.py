import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)

REQUEST_TOPIC = "s9004_vulnerability_requests"
RESPONSE_TOPIC = "s9004_vulnerability_responses"


class KafkaVulnerabilityClient:
    def __init__(self):
        self.producer = None
        self.consumer = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=BOOTSTRAP_SERVERS,
        )

        self.consumer = AIOKafkaConsumer(
            RESPONSE_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"s9004-client-{uuid.uuid4()}",
            auto_offset_reset="latest",
            enable_auto_commit=False,
        )

        await self.producer.start()
        await self.consumer.start()

        print(
            f"[CLIENT] Listening on {RESPONSE_TOPIC}",
            flush=True,
        )

    async def stop(self):
        if self.consumer is not None:
            await self.consumer.stop()

        if self.producer is not None:
            await self.producer.stop()

    async def request(
        self,
        operation,
        data,
        correlation_id=None,
    ):
        correlation_id = correlation_id or str(uuid.uuid4())

        message = {
            "correlation_id": correlation_id,
            "reply_to": RESPONSE_TOPIC,
            "operation": operation,
            "data": data,
        }

        print(
            f"[CLIENT] Sending {operation} to {REQUEST_TOPIC}",
            flush=True,
        )
        print(
            f"[CLIENT] correlation_id={correlation_id}",
            flush=True,
        )
        print(
            f"[CLIENT] message={json.dumps(message)}",
            flush=True,
        )

        await self.producer.send_and_wait(
            REQUEST_TOPIC,
            json.dumps(message).encode("utf-8"),
        )

        print(
            f"[CLIENT] Request sent to {REQUEST_TOPIC}",
            flush=True,
        )

        async for record in self.consumer:
            response = json.loads(
                record.value.decode("utf-8"),
            )

            if response.get("correlation_id") != correlation_id:
                continue

            print(
                f"[CLIENT] Response received from {RESPONSE_TOPIC}",
                flush=True,
            )
            print(
                f"[CLIENT] response={json.dumps(response)}",
                flush=True,
            )

            await self.consumer.commit()
            return response


async def main():
    client = KafkaVulnerabilityClient()
    await client.start()

    try:
        response = await client.request(
            "CREATE_VULNERABILITY",
            {
                "vulnerability_code": "HW8-VULN-001",
                "vulnerability_title": "Kafka test vulnerability",
                "package_name": "package-0",
                "submitter_email": "student@example.com",
                "description": (
                    "This is a sufficiently long vulnerability description for testing."
                ),
                "category": "Input Validation",
                "terms_accepted": True,
            },
        )

        print(
            f"[CLIENT] Final result: {response}",
            flush=True,
        )
    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
