import json
import time
from pathlib import Path

import agent_runner


CASES = [
    {
        "id": "A",
        "prompt": (
            "Search for a seeded vulnerability, then use "
            "the first result ID to retrieve its full details. "
            "Make both tool calls before answering."
        ),
        "required_tool_calls": 2,
    },
    {
        "id": "B",
        "prompt": (
            "First get an aggregate summary of the vulnerability "
            "database. Then search for package-0 as one concrete "
            "supporting example. Make both tool calls before answering."
        ),
        "required_tool_calls": 2,
    },
    {
        "id": "C",
        "prompt": (
            "Search for package-0 first. Then retrieve details for "
            "vulnerability IDs 10002 and 9752 and compare them. "
            "Make all three tool calls before answering."
        ),
        "required_tool_calls": 3,
    },
]


OUTPUT_PATH = Path("reports/hw07/raw/agent_reliability.json")


def classify_failure(
    result: dict,
    required_tool_calls: int,
) -> str:
    stop_reason = result.get(
        "stop_reason",
        "",
    )

    error = result.get(
        "error",
        "",
    ).lower()

    tool_calls = result.get(
        "tool_calls",
        0,
    )

    if stop_reason == "repair_failed":
        if "unknown tool" in error:
            return "unknown tool"

        return "malformed arguments"

    if tool_calls == 0:
        return "text when a tool was required"

    if stop_reason == "budget_exhausted" or tool_calls < required_tool_calls:
        return "lost multi-step chain"

    return "none"


def run_attempt(
    case: dict,
    mode: str,
    attempt_number: int,
) -> dict:
    if mode == "before_repair":
        agent_runner.MAX_REPAIR_ATTEMPTS = 0
    else:
        agent_runner.MAX_REPAIR_ATTEMPTS = 1

    started = time.perf_counter()

    result = agent_runner.run_agent(
        case["prompt"],
        max_steps=6,
        log_path="reports/hw07/RUN_LOG.txt",
    )

    latency_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    tool_calls = result.get(
        "tool_calls",
        0,
    )

    required_tool_calls = case["required_tool_calls"]

    success = (
        result.get("stop_reason") == "model_finished"
        and tool_calls >= required_tool_calls
    )

    return {
        "attempt": attempt_number,
        "mode": mode,
        "case_id": case["id"],
        "required_tool_calls": required_tool_calls,
        "tool_calls": tool_calls,
        "stop_reason": result.get("stop_reason"),
        "latency_ms": latency_ms,
        "success": success,
        "failure_type": (
            "none"
            if success
            else classify_failure(
                result,
                required_tool_calls,
            )
        ),
        "final": result.get(
            "final",
            "",
        ),
        "steps": result.get(
            "steps",
            [],
        ),
        "error": result.get(
            "error",
            "",
        ),
    }


def summarize(
    attempts: list[dict],
    mode: str,
) -> dict:
    selected = [item for item in attempts if item["mode"] == mode]

    well_formed = sum(item["tool_calls"] > 0 for item in selected)

    successful = sum(item["success"] for item in selected)

    failure_counts = {}

    for item in selected:
        failure_type = item["failure_type"]

        if failure_type != "none":
            failure_counts[failure_type] = (
                failure_counts.get(
                    failure_type,
                    0,
                )
                + 1
            )

    return {
        "mode": mode,
        "attempt_count": len(selected),
        "well_formed_call_count": well_formed,
        "well_formed_call_rate": round(
            well_formed / len(selected),
            3,
        ),
        "successful_task_count": successful,
        "task_success_rate": round(
            successful / len(selected),
            3,
        ),
        "failure_counts": failure_counts,
        "mean_latency_ms": round(
            sum(item["latency_ms"] for item in selected) / len(selected),
            2,
        ),
    }


def main() -> None:
    attempts = []
    attempt_number = 0

    for mode in [
        "before_repair",
        "after_repair",
    ]:
        for offset in range(10):
            case = CASES[offset % len(CASES)]

            attempt_number += 1

            print(f"Running {mode} attempt {attempt_number}/20 case={case['id']}")

            result = run_attempt(
                case,
                mode,
                attempt_number,
            )

            attempts.append(result)

            print(
                f"  success={result['success']} "
                f"tool_calls={result['tool_calls']} "
                f"failure={result['failure_type']}"
            )

    output = {
        "homework": "DATA-260 Homework 7",
        "model": "qwen3:8b",
        "cases": CASES,
        "summary": {
            "before_repair": summarize(
                attempts,
                "before_repair",
            ),
            "after_repair": summarize(
                attempts,
                "after_repair",
            ),
        },
        "attempts": attempts,
    }

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            output["summary"],
            indent=2,
        )
    )

    print(f"Saved results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
