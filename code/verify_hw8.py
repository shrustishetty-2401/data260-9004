import json
import subprocess
import urllib.request
from pathlib import Path


REPORT_DIR = Path("reports/hw08")
RAW_DIR = REPORT_DIR / "raw"
VERIFY_PATH = REPORT_DIR / "verification.json"


def check_file(path):
    return path.exists()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def api_health_check():
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:8004/health",
            timeout=5,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8"),
            )

        return response.status == 200 and payload.get("status") == "ok"
    except Exception:
        return False


def main():
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        commit_hash = "unavailable"

    duplicate = load_json(
        RAW_DIR / "duplicate_delivery.json",
    )
    poison = load_json(
        RAW_DIR / "poison_message.json",
    )
    consumer_death = load_json(
        RAW_DIR / "consumer_death.json",
    )
    ordering = load_json(
        RAW_DIR / "ordering_results.json",
    )
    pipeline = load_json(
        RAW_DIR / "part2_pipeline_result.json",
    )
    part1_errors = load_json(
        RAW_DIR / "part1_error_tests.json",
    )

    checks = {
        "api_health": api_health_check(),
        "part1_create_get_evidence": check_file(
            RAW_DIR.parent / "RUN_LOG.txt",
        ),
        "part1_error_tests": (
            part1_errors["unknown_operation"]["success"] is False
            and part1_errors["unknown_entity"]["success"] is False
            and part1_errors["invalid_create"]["success"] is False
        ),
        "part2_pipeline_approved": (pipeline.get("status") == "approved"),
        "duplicate_delivery_prevented": (
            duplicate.get("duplicate_prevented") is True
            and duplicate.get("same_entity_id") is True
        ),
        "consumer_death_recovered": (
            consumer_death.get(
                "recovered_after_restart",
            )
            is True
        ),
        "poison_dead_letter": (
            poison.get("moved_to_dead_letter") is True
            and poison.get("retry_count") == 3
        ),
        "keyed_ordering_preserved": (ordering.get("keyed_order_preserved") is True),
        "required_evidence_directory": check_file(
            REPORT_DIR / "evidence",
        ),
    }

    verification = {
        "homework": "DATA-260 Homework 8",
        "sid4": 9004,
        "commit_hash": commit_hash,
        "model": "qwen3:8b",
        "port_base": 8004,
        "prefix": "s9004",
        "seed": 9004,
        "verify_seed": 269004,
        "domain_id": 4,
        "checks": checks,
        "all_passed": all(checks.values()),
    }

    VERIFY_PATH.write_text(
        json.dumps(verification, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(verification, indent=2))
    print(f"Saved verification to {VERIFY_PATH}")

    if not verification["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
