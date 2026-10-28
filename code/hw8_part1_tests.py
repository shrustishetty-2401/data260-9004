import asyncio
import json
from pathlib import Path

from hw8_client import KafkaVulnerabilityClient


OUTPUT_PATH = Path(
    "reports/hw08/raw/part1_error_tests.json",
)


async def main():
    client = KafkaVulnerabilityClient()
    await client.start()

    results = {}

    try:
        results["unknown_operation"] = await client.request(
            "DELETE_VULNERABILITY",
            {},
        )

        results["unknown_entity"] = await client.request(
            "GET_VULNERABILITY",
            {
                "entity_id": "does-not-exist",
            },
        )

        results["invalid_create"] = await client.request(
            "CREATE_VULNERABILITY",
            {
                "vulnerability_code": "",
                "vulnerability_title": "",
                "package_name": "",
                "submitter_email": "invalid-email",
                "description": "too short",
                "category": "",
                "terms_accepted": False,
            },
        )

    finally:
        await client.stop()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    OUTPUT_PATH.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(results, indent=2))
    print(f"Saved results to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
