import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


BASE_URL = os.getenv(
    "HW6_BASE_URL",
    "http://127.0.0.1:8004",
)

OUTPUT_PATH = Path(
    "reports/hw06/verification.json"
)


def request_json(
    method: str,
    path: str,
    body: dict | None = None,
) -> tuple[int, dict]:
    data = None
    headers = {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(
        request,
        timeout=30,
    ) as response:
        content = response.read().decode("utf-8")

        if not content:
            return response.status, {}

        return response.status, json.loads(content)


def main() -> None:
    checks = []

    try:
        status, payload = request_json(
            "GET",
            "/health",
        )

        checks.append(
            {
                "name": "FastAPI health endpoint",
                "passed": (
                    status == 200
                    and payload.get("status") == "ok"
                ),
            }
        )

        status, documents = request_json(
            "GET",
            "/api/documents",
        )

        checks.append(
            {
                "name": "MongoDB document list endpoint",
                "passed": (
                    status == 200
                    and isinstance(documents, list)
                ),
            }
        )

        status, document = request_json(
            "POST",
            "/api/documents",
            {
                "title": "HW6 verification document",
                "description": "Temporary smoke-test document.",
                "severity": "low",
                "status": "open",
                "discovered_at": (
                    "2026-10-13T17:00:00Z"
                ),
            },
        )

        created_id = document.get("id")

        checks.append(
            {
                "name": "MongoDB document create endpoint",
                "passed": (
                    status == 201
                    and bool(created_id)
                ),
            }
        )

        if created_id:
            delete_status, _ = request_json(
                "DELETE",
                f"/api/documents/{created_id}",
            )

            checks.append(
                {
                    "name": "MongoDB document delete endpoint",
                    "passed": delete_status == 204,
                }
            )

        status, memory = request_json(
            "GET",
            "/api/memory/student-9004",
        )

        checks.append(
            {
                "name": "Memory endpoint",
                "passed": (
                    status == 200
                    and "messages" in memory
                ),
            }
        )

        status, aggregate = request_json(
            "GET",
            "/api/aggregate/student-9004",
        )

        checks.append(
            {
                "name": "Aggregate endpoint",
                "passed": (
                    status == 200
                    and "daily_message_counts"
                    in aggregate
                ),
            }
        )

    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        json.JSONDecodeError,
        KeyError,
    ) as error:
        checks.append(
            {
                "name": "Smoke test execution",
                "passed": False,
                "error": str(error),
            }
        )

    commit_hash = subprocess.check_output(
        [
            "git",
            "rev-parse",
            "HEAD",
        ],
        text=True,
    ).strip()

    result = {
        "homework": "HW6",
        "sid4": 9004,
        "commit_hash": commit_hash,
        "model": "qwen3:8b",
        "configuration": {
            "PORT_BASE": 8004,
            "PREFIX": "s9004",
            "DOMAIN_ID": 4,
        },
        "SEED": 9004,
        "VERIFY_SEED": 269004,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat(),
        "checks": checks,
        "passed": all(
            check["passed"]
            for check in checks
        ),
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            result,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()