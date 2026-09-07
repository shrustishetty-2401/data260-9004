import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "reports/hw02/verification.json"
PORT = 8004


def check_api():
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api:app",
            "--app-dir",
            "code",
            "--host",
            "127.0.0.1",
            "--port",
            str(PORT),
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen(
                    f"http://127.0.0.1:{PORT}/api/reports",
                    timeout=2,
                ) as response:
                    body = json.loads(response.read().decode("utf-8"))

                    return {
                        "name": "FastAPI reports endpoint responds",
                        "passed": response.status == 200
                        and isinstance(body, list),
                    }

            except Exception:
                time.sleep(1)

        return {
            "name": "FastAPI reports endpoint responds",
            "passed": False,
        }

    finally:
        server.terminate()
        server.wait(timeout=10)


def check_langgraph():
    completed = subprocess.run(
        [
            sys.executable,
            "code/langgraph_demo.py",
            "--title",
            "Verification test",
            "--content",
            "This verification input checks that the graph completes safely.",
        ],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        timeout=180,
    )

    return {
        "name": "LangGraph completes without hanging",
        "passed": completed.returncode == 0
        and "Final state" in completed.stdout,
    }


def main():
    checks = []

    try:
        checks.append(check_api())
    except Exception as error:
        checks.append(
            {
                "name": "FastAPI reports endpoint responds",
                "passed": False,
                "error": str(error),
            }
        )

    try:
        checks.append(check_langgraph())
    except Exception as error:
        checks.append(
            {
                "name": "LangGraph completes without hanging",
                "passed": False,
                "error": str(error),
            }
        )

    verification = {
        "homework": "DATA-260 Homework 2",
        "sid4": 9004,
        "commit_hash": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip(),
        "model": "qwen3:8b",
        "seed": 9004,
        "verify_seed": 269004,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "all_passed": all(check["passed"] for check in checks),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(verification, file, indent=2)

    print(json.dumps(verification, indent=2))


if __name__ == "__main__":
    main()