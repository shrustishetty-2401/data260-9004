import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from aiokafka import AIOKafkaConsumer
from deepeval.metrics import GEval
from deepeval.models import OllamaModel
from deepeval.test_case import LLMTestCase, LLMTestCaseParams


BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS",
    "localhost:29092",
)
PREFIX = os.getenv("PREFIX", "s9004")
JUDGE_MODEL_NAME = os.getenv("JUDGE_MODEL", "qwen3:8b")
OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
)
EVALUATION_TIMEOUT_SECONDS = float(os.getenv("EVALUATION_TIMEOUT_SECONDS", "20"))

TASKS_TOPIC = f"{PREFIX}_tasks"
DRAFTS_TOPIC = f"{PREFIX}_drafts"
FINAL_TOPIC = f"{PREFIX}_final"

OUTPUT_PATH = Path(
    "reports/hw10/raw/pipeline_evaluation.json",
)


def build_metrics():
    judge_model = OllamaModel(
        model=JUDGE_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
    )

    plan_quality = GEval(
        name="Plan Quality",
        criteria=(
            "Evaluate whether the planner created a useful, coherent plan "
            "that identifies the main goal, relevant facts, organization, "
            "and an appropriate writing approach."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=judge_model,
    )

    writer_helpfulness = GEval(
        name="Writer Helpfulness",
        criteria=(
            "Evaluate whether the writer draft is accurate, relevant, "
            "clear, useful, and responsive to the original question. "
            "Penalize unsupported claims and unnecessary content."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=judge_model,
    )

    final_helpfulness = GEval(
        name="Final Answer Helpfulness",
        criteria=(
            "Evaluate whether the final answer directly answers the original "
            "question, is accurate and relevant, and is clear and useful "
            "to the user."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        model=judge_model,
    )

    return plan_quality, writer_helpfulness, final_helpfulness


async def collect_messages(trace_id: str, timeout_seconds: float = 30.0):
    group_id = f"{PREFIX}-hw10-evaluator-{trace_id[:8]}"
    consumers = [
        AIOKafkaConsumer(
            TASKS_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"{group_id}-tasks",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        ),
        AIOKafkaConsumer(
            DRAFTS_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"{group_id}-drafts",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        ),
        AIOKafkaConsumer(
            FINAL_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=f"{group_id}-final",
            auto_offset_reset="earliest",
            enable_auto_commit=False,
        ),
    ]

    messages = {}

    for consumer in consumers:
        await consumer.start()

    try:
        deadline = time.monotonic() + timeout_seconds

        while len(messages) < 3 and time.monotonic() < deadline:
            remaining_ms = max(
                100,
                int((deadline - time.monotonic()) * 1000),
            )

            for name, consumer in zip(
                ("plan", "draft", "final"),
                consumers,
            ):
                records = await consumer.getmany(
                    timeout_ms=min(500, remaining_ms),
                    max_records=100,
                )

                for topic_records in records.values():
                    for record in topic_records:
                        try:
                            message = json.loads(
                                record.value.decode("utf-8"),
                            )
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            continue

                        if message.get("correlation_id") == trace_id:
                            messages[name] = message
                            break

    finally:
        for consumer in consumers:
            await consumer.stop()

    missing = [name for name in ("plan", "draft", "final") if name not in messages]
    if missing:
        raise TimeoutError("Timed out waiting for stages: " + ", ".join(missing))

    return messages


def judge_score(metric, test_case):
    metric.measure(test_case)
    normalized_score = float(metric.score or 0.0)
    score_1_to_5 = 1.0 + (4.0 * normalized_score)

    return {
        "score": round(score_1_to_5, 3),
        "normalized_score": round(normalized_score, 4),
        "reason": (metric.reason or "").strip(),
    }


async def evaluate_stage(metric, test_case):
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(judge_score, metric, test_case),
            timeout=EVALUATION_TIMEOUT_SECONDS,
        )
        return result
    except Exception as error:
        return {
            "score": None,
            "normalized_score": None,
            "reason": "",
            "error": f"{type(error).__name__}: {error}",
        }


async def main(trace_id: str):
    messages = await collect_messages(trace_id)

    question = messages["final"].get(
        "question",
        messages["draft"].get(
            "question",
            messages["plan"].get("question", ""),
        ),
    )
    plan = messages["plan"].get("plan", "")
    draft = messages["draft"].get("draft", "")
    final_answer = messages["final"].get("answer", "")

    plan_metric, writer_metric, final_metric = build_metrics()

    plan_case = LLMTestCase(
        input=question,
        actual_output=plan,
    )
    writer_case = LLMTestCase(
        input=question,
        actual_output=draft,
    )
    final_case = LLMTestCase(
        input=question,
        actual_output=final_answer,
    )

    plan_result, writer_result, final_result = await asyncio.gather(
        evaluate_stage(plan_metric, plan_case),
        evaluate_stage(writer_metric, writer_case),
        evaluate_stage(final_metric, final_case),
    )

    draft_score = writer_result.get("score")
    final_score = final_result.get("score")
    improvement = None
    interpretation = "Unable to compare because one score is missing."

    if draft_score is not None and final_score is not None:
        improvement = round(final_score - draft_score, 3)
        if improvement > 0:
            interpretation = "The Reviewer improved the judged helpfulness score."
        elif improvement < 0:
            interpretation = "The Reviewer lowered the judged helpfulness score."
        else:
            interpretation = "The Reviewer did not change the judged helpfulness score."

    result = {
        "trace_id": trace_id,
        "judge_model": JUDGE_MODEL_NAME,
        "score_scale": "1-5",
        "question": question,
        "messages": messages,
        "plan_quality": plan_result,
        "writer_helpfulness": writer_result,
        "final_answer_helpfulness": final_result,
        "final_vs_draft": {
            "draft_score": draft_score,
            "final_score": final_score,
            "difference": improvement,
            "interpretation": interpretation,
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(result, indent=2))
    print(f"Saved evaluation to {OUTPUT_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate one HW10 Planner-Writer-Reviewer trace."
    )
    parser.add_argument(
        "--trace-id",
        required=True,
        help="The shared HW8 correlation_id for the request.",
    )
    args = parser.parse_args()

    try:
        asyncio.run(main(args.trace_id))
    except KeyboardInterrupt:
        raise SystemExit("Evaluation cancelled.")
    except TimeoutError as error:
        raise SystemExit(f"Evaluation failed: {error}")
