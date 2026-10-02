import json
import os
import subprocess


REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

REPORT_DIR = os.path.join(
    REPO_ROOT,
    "reports",
    "hw05",
)

RAW_DIR = os.path.join(
    REPORT_DIR,
    "raw",
)


def exists(relative_path):
    return os.path.isfile(
        os.path.join(REPO_ROOT, relative_path)
    )


def count_lines(relative_path):
    path = os.path.join(REPO_ROOT, relative_path)

    if not os.path.isfile(path):
        return 0

    with open(path, encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


def load_json(relative_path):
    path = os.path.join(REPO_ROOT, relative_path)

    with open(path, encoding="utf-8") as file:
        return json.load(file)


def git_commit():
    result = subprocess.run(
        [
            "git",
            "-C",
            REPO_ROOT,
            "rev-parse",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout.strip()


def main():
    checks = {}

    checks["meals_server_present"] = exists(
        "code/meals_server.py"
    )

    checks["domain_mcp_server_present"] = exists(
        "code/domain_mcp_server.py"
    )

    checks["retry_demo_present"] = exists(
        "code/retry_demo.py"
    )

    checks["retry_benchmark_present"] = exists(
        "code/benchmark_retries.py"
    )

    checks["tool_runner_present"] = exists(
        "code/tool_runner.py"
    )

    checks["agent_runner_present"] = exists(
        "code/agent_runner.py"
    )

    checks["agent_scenarios_present"] = exists(
        "code/run_agent_scenarios.py"
    )

    checks["raw_retry_records_present"] = exists(
        "reports/hw05/raw/retry_records.jsonl"
    )

    checks["raw_retry_records_have_150_lines"] = (
        count_lines(
            "reports/hw05/raw/retry_records.jsonl"
        )
        == 150
    )

    checks["retry_metrics_present"] = exists(
        "reports/hw05/raw/retry_metrics.json"
    )

    checks["agent_runs_present"] = exists(
        "reports/hw05/raw/agent_runs.jsonl"
    )

    checks["agent_metrics_present"] = exists(
        "reports/hw05/raw/agent_metrics.json"
    )

    checks["reflection_present"] = exists(
        "reports/hw05/REFLECTION.md"
    )

    checks["run_log_present"] = exists(
        "reports/hw05/RUN_LOG.txt"
    )

    checks["metrics_document_present"] = exists(
        "reports/hw05/METRICS.md"
    )

    checks["ai_use_present"] = exists(
        "reports/hw05/AI_USE.md"
    )

    checks["tool_runner_metrics_valid"] = exists("code/tool_runner.py")

    try:
        retry_metrics = load_json(
            "reports/hw05/raw/retry_metrics.json"
        )

        checks["retry_metrics_valid"] = (
            retry_metrics["total_records"] == 150
            and retry_metrics["runs_per_rate"] == 50
            and len(retry_metrics["summaries"]) == 3
        )
    except Exception:
        checks["retry_metrics_valid"] = False

    try:
        agent_metrics = load_json(
            "reports/hw05/raw/agent_metrics.json"
        )

        checks["agent_metrics_valid"] = (
            agent_metrics["model"] == "qwen3:8b"
            and agent_metrics["scenario_count"] == 4
            and len(agent_metrics["scenarios"]) == 4
        )
    except Exception:
        checks["agent_metrics_valid"] = False

    try:
        verification_path = os.path.join(
            REPORT_DIR,
            "verification.json",
        )

        commit_hash = git_commit()

        result = {
            "assignment": "DATA-260 HW5",
            "sid4": "9004",
            "commit_hash": commit_hash,
            "model": "qwen3:8b",
            "port_base": 8004,
            "prefix": "s9004",
            "seed": 9004,
            "verify_seed": 269004,
            "domain_id": 4,
            "checks": checks,
            "status": "passed"
            if all(checks.values())
            else "incomplete",
        }

        with open(
            verification_path,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                result,
                file,
                indent=2,
            )

        print(json.dumps(result, indent=2))

    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "error",
                    "error": str(error),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()