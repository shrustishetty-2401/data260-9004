import asyncio
import json
import os
import uuid

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:9092",
)

REQUEST_TOPIC = "s9004_vulnerability_requests"
DEFAULT_RESPONSE_TOPIC = "s9004_vulnerability_responses"

entities = {}
processed_requests = {}


def error_response(correlation_id, message):
    return {
        "correlation_id": correlation_id,
        "success": False,
        "error": message,
    }


def validate_vulnerability(data):
    required_fields = {
        "vulnerability_code",
        "vulnerability_title",
        "package_name",
        "submitter_email",
        "description",
        "category",
        "terms_accepted",
    }

    if not isinstance(data, dict):
        return "data must be an object"

    missing = required_fields - set(data)
    if missing:
        return f"Missing required fields: {sorted(missing)}"

    for field in required_fields - {"terms_accepted"}:
        if not isinstance(data[field], str) or not data[field].strip():
            return f"{field} must be a non-empty string"

    if "@" not in data["submitter_email"]:
        return "submitter_email must be a valid email"

    if len(data["description"].strip()) < 26:
        return "description must contain at least 26 characters"

    if data["terms_accepted"] is not True:
        return "terms_accepted must be true"

    return None


def process_request(message):
    correlation_id = message.get("correlation_id")

    if not isinstance(correlation_id, str) or not correlation_id:
        return {
            "correlation_id": correlation_id,
            "success": False,
            "error": "correlation_id is required",
        }

    if correlation_id in processed_requests:
        print(
            f"[WORKER] Duplicate correlation_id ignored: {correlation_id}",
            flush=True,
        )
        return processed_requests[correlation_id]

    operation = message.get("operation")
    data = message.get("data")

    if operation == "CREATE_VULNERABILITY":
        validation_error = validate_vulnerability(data)

        if validation_error:
            response = error_response(
                correlation_id,
                validation_error,
            )
        else:
            vulnerability_id = str(uuid.uuid4())

            entity = {
                "entity_id": vulnerability_id,
                **data,
            }

            entities[vulnerability_id] = entity

            response = {
                "correlation_id": correlation_id,
                "success": True,
                "entity_id": vulnerability_id,
                "message": "Entity created",
            }

    elif operation == "GET_VULNERABILITY":
        entity_id = data.get("entity_id") if isinstance(data, dict) else None

        if entity_id not in entities:
            response = error_response(
                correlation_id,
                "Entity not found",
            )
        else:
            response = {
                "correlation_id": correlation_id,
                "success": True,
                "entity": entities[entity_id],
            }

    else:
        response = error_response(
            correlation_id,
            "Unknown operation",
        )

    processed_requests[correlation_id] = response
    return response


async def run_worker():
    consumer = AIOKafkaConsumer(
        REQUEST_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id="s9004-vulnerability-worker",
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
    )

    await consumer.start()
    await producer.start()

    print(
        "Consumer is ready and listening...",
        flush=True,
    )
    print(
        f"Listening on {REQUEST_TOPIC}",
        flush=True,
    )

    try:
        async for record in consumer:
            message = json.loads(record.value.decode("utf-8"))

            print(
                f"[WORKER] Received operation="
                f"{message.get('operation')} "
                f"correlation_id={message.get('correlation_id')}",
                flush=True,
            )

            response = process_request(message)

            reply_to = message.get(
                "reply_to",
                DEFAULT_RESPONSE_TOPIC,
            )

            print(
                f"[WORKER] Sending response to {reply_to} "
                f"correlation_id={response.get('correlation_id')}",
                flush=True,
            )

            await producer.send_and_wait(
                reply_to,
                json.dumps(response).encode("utf-8"),
            )

            await consumer.commit()

            print(
                f"[WORKER] Completed operation="
                f"{message.get('operation')} "
                f"success={response.get('success')}",
                flush=True,
            )

    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
