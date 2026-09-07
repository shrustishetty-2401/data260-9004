import argparse
import io
import json
import sys
import time
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = REPO_ROOT / "code"

sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(CODE_DIR))

import langgraph_demo


def load_input(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def classify_result(final_state: dict, ceiling: int) -> str:
    if final_state.get("final_output"):
        turns = final_state.get("turn_count", 0)

        if turns == 1:
            return "valid first attempt"
        if turns == 2:
            return "valid after one retry"
        return "valid after two or more retries"

    if final_state.get("turn_count", 0) >= ceiling:
        return "abandoned at the ceiling"

    return "incomplete"


def run_once(input_data: dict, ceiling: int) -> dict:
    langgraph_demo.TURN_CEILING = ceiling
    langgraph_demo.FORCE_REVIEWER_FAILURE = False

    initial_state = {
        "title": input_data["title"],
        "content": input_data["content"],
        "email": input_data.get("email", "student@sjsu.edu"),
        "strict": True,
        "task": "Create exactly three tags and a summary.",
        "turn_count": 0,
    }

    graph = langgraph_demo.build_graph()
    final_state = dict(initial_state)

    started = time.perf_counter()

    with redirect_stdout(io.StringIO()):
        for event in graph.stream(initial_state):
            for update in event.values():
                if isinstance(update, dict):
                    final_state.update(update)

    latency_ms = round((time.perf_counter() - started) * 1000, 2)

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "ceiling": ceiling,
        "latency_ms": latency_ms,
        "classification": classify_result(final_state, ceiling),
        "turn_count": final_state.get("turn_count", 0),
        "final_output": final_state.get("final_output"),
        "validation_error": final_state.get("validation_error", ""),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Run repeatable Homework 2 LangGraph experiments."
    )

    parser.add_argument(
        "--input",
        default="reports/hw02/cases/schema_input.json",
    )
    parser.add_argument(
        "--runs",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--ceiling",
        type=int,
        required=True,
    )
    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    input_path = REPO_ROOT / args.input
    output_path = REPO_ROOT / args.output

    input_data = load_input(input_path)
    results = []

    print(f"Input: {input_path}")
    print(f"Runs: {args.runs}")
    print(f"Turn ceiling: {args.ceiling}")

    for run_number in range(1, args.runs + 1):
        result = run_once(input_data, args.ceiling)
        result["run_number"] = run_number
        results.append(result)

        print(
            f"Run {run_number}/{args.runs}: "
            f"{result['classification']}, "
            f"turns={result['turn_count']}, "
            f"latency_ms={result['latency_ms']}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    experiment = {
        "homework": "DATA-260 Homework 2",
        "input_file": str(args.input),
        "input": input_data,
        "runs": results,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(experiment, file, indent=2)

    print(f"Saved results to: {output_path}")


if __name__ == "__main__":
    main()