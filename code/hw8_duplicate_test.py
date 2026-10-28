import asyncio
import json
import uuid
from pathlib import Path

from hw8_client import KafkaVulnerabilityClient


OUTPUT_PATH = Path(
    "reports/hw08/raw/duplicate_delivery.json",
)


async def main():
    client = KafkaVulnerabilityClient()
    await client.start()

    correlation_id = str(uuid.uuid4())

    payload = {
        "vulnerability_code": "HW8-DUPLICATE-001",
        "vulnerability_title": "Duplicate delivery test",
        "package_name": "package-duplicate",
        "submitter_email": "student@example.com",
        "description": (
            "This description is long enough for duplicate delivery testing."
        ),
        "category": "Dependency Risk",
        "terms_accepted": True,
    }

    try:
        print("[DUPLICATE] Sending original request")
        first_response = await client.request(
            "CREATE_VULNERABILITY",
            payload,
            correlation_id=correlation_id,
        )

        print("[DUPLICATE] Replaying identical request")
        second_response = await client.request(
            "CREATE_VULNERABILITY",
            payload,
            correlation_id=correlation_id,
        )

    finally:
        await client.stop()

    first_entity_id = first_response.get("entity_id")
    second_entity_id = second_response.get("entity_id")

    result = {
        "correlation_id": correlation_id,
        "first_response": first_response,
        "second_response": second_response,
        "same_entity_id": (
            first_entity_id is not None and first_entity_id == second_entity_id
        ),
        "duplicate_prevented": (first_response == second_response),
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
