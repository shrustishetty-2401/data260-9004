import asyncio
import json

from hw8_client import KafkaVulnerabilityClient


async def main():
    client = KafkaVulnerabilityClient()
    await client.start()

    vulnerability_data = {
        "vulnerability_code": "HW8-DEMO-001",
        "vulnerability_title": "Kafka demonstration vulnerability",
        "package_name": "package-0",
        "submitter_email": "student@example.com",
        "description": (
            "This description is long enough for the HW8 "
            "vulnerability validation requirement."
        ),
        "category": "Input Validation",
        "terms_accepted": True,
    }

    try:
        print("\n=== CREATE_VULNERABILITY SEQUENCE ===")

        create_response = await client.request(
            "CREATE_VULNERABILITY",
            vulnerability_data,
        )

        print(
            "[DEMO] CREATE response:",
            json.dumps(create_response, indent=2),
        )

        if not create_response.get("success"):
            print("[DEMO] CREATE failed")
            return

        entity_id = create_response["entity_id"]
        create_correlation_id = create_response["correlation_id"]

        print("\n=== GET_VULNERABILITY SEQUENCE ===")

        get_response = await client.request(
            "GET_VULNERABILITY",
            {"entity_id": entity_id},
        )

        print(
            "[DEMO] GET response:",
            json.dumps(get_response, indent=2),
        )

        get_correlation_id = get_response.get("correlation_id")
        retrieved_entity = get_response.get("entity")

        print(
            f"\n[DEMO] CREATE correlation_id preserved: {bool(create_correlation_id)}"
        )
        print(f"[DEMO] GET correlation_id preserved: {bool(get_correlation_id)}")
        print(f"[DEMO] GET returned entity: {retrieved_entity is not None}")
        print(f"[DEMO] generated entity_id: {entity_id}")

    finally:
        await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
