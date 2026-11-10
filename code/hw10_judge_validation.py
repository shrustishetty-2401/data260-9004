import csv
import json
import os
import time
from pathlib import Path

from deepeval.metrics import GEval
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


CASES_PATH = Path("reports/hw10/data/eval_cases.json")
LABELS_PATH = Path("reports/hw10/data/human_labels.csv")
OUTPUT_PATH = Path("reports/hw10/raw/judge_validation.json")

JUDGE_MODEL_NAME = os.getenv("JUDGE_MODEL", "qwen3:8b")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)
REPEAT_COUNT = 3


def rank_values(values):
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    position = 0

    while position < len(ordered):
        end = position
        while end + 1 < len(ordered) and ordered[end + 1][1] == ordered[position][1]:
            end += 1

        average_rank = (position + 1 + end + 1) / 2
        for index in range(position, end + 1):
            ranks[ordered[index][0]] = average_rank
        position = end + 1

    return ranks


def spearman_correlation(left, right):
    if len(left) != len(right) or len(left) < 2:
        return None

    left_ranks = rank_values(left)
    right_ranks = rank_values(right)
    left_mean = sum(left_ranks) / len(left_ranks)
    right_mean = sum(right_ranks) / len(right_ranks)

    numerator = sum(
        (left_rank - left_mean) * (right_rank - right_mean)
        for left_rank, right_rank in zip(left_ranks, right_ranks)
    )
    left_sum = sum((rank - left_mean) ** 2 for rank in left_ranks)
    right_sum = sum((rank - right_mean) ** 2 for rank in right_ranks)

    if left_sum == 0 or right_sum == 0:
        return None

    return numerator / (left_sum * right_sum) ** 0.5


def load_inputs():
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    with LABELS_PATH.open(newline="", encoding="utf-8") as file:
        labels = {
            row["case_id"]: int(row["human_helpfulness_label"])
            for row in csv.DictReader(file)
        }

    if len(cases) != 20 or len(labels) != 20:
        raise ValueError("Expected exactly 20 cases and 20 labels.")

    return cases, labels


def build_metric():
    judge_model = OllamaModel(
        model=JUDGE_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
    )

    return GEval(
        name="Writer Helpfulness",
        criteria=(
            "Evaluate whether the Writer draft is accurate, relevant, clear, "
            "useful, and responsive to the question. Penalize generic planning "
            "language that does not answer the question."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=judge_model,
        async_mode=False,
    )


def judge_case(metric, case):
    started = time.perf_counter()
    test_case = LLMTestCase(
        input=case["question"],
        actual_output=case["writer_draft"],
    )
    metric.measure(test_case)
    normalized_score = float(metric.score or 0.0)
    score = 1.0 + (4.0 * normalized_score)

    return {
        "case_id": case["case_id"],
        "question": case["question"],
        "human_label": None,
        "judge_score": round(score, 3),
        "normalized_score": round(normalized_score, 4),
        "reason": (metric.reason or "").strip(),
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def summarize(rows):
    human = [row["human_label"] for row in rows]
    judge = [row["judge_score"] for row in rows]
    differences = [abs(a - b) for a, b in zip(human, judge)]

    return {
        "spearman_correlation": spearman_correlation(human, judge),
        "mean_absolute_difference": sum(differences) / len(differences),
        "case_count": len(rows),
    }


def main():
    cases, labels = load_inputs()
    all_repeats = []

    for repeat_number in range(1, REPEAT_COUNT + 1):
        print(f"Starting judge repeat {repeat_number}/{REPEAT_COUNT}")
        metric = build_metric()
        rows = []

        for number, case in enumerate(cases, start=1):
            print(f"  repeat={repeat_number} case={number}/20", flush=True)
            row = judge_case(metric, case)
            row["human_label"] = labels[case["case_id"]]
            rows.append(row)

        all_repeats.append(
            {
                "repeat": repeat_number,
                "summary": summarize(rows),
                "cases": rows,
            }
        )

    score_changes = []
    for case_index in range(len(cases)):
        scores = [repeat["cases"][case_index]["judge_score"] for repeat in all_repeats]
        for left, right in zip(scores, scores[1:]):
            score_changes.append(abs(left - right))

    output = {
        "judge_model": JUDGE_MODEL_NAME,
        "ollama_base_url": OLLAMA_BASE_URL,
        "score_scale": "1-5",
        "repeat_count": REPEAT_COUNT,
        "case_count": len(cases),
        "repeated_score_changes": sum(change > 0 for change in score_changes),
        "repeat_comparison_count": len(score_changes),
        "mean_absolute_repeat_change": (
            sum(score_changes) / len(score_changes) if score_changes else 0.0
        ),
        "maximum_absolute_repeat_change": max(score_changes, default=0.0),
        "repeats": all_repeats,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    print(f"Saved judge validation to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
