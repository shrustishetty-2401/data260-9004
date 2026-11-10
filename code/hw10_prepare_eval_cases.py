import csv
import json
import uuid
from pathlib import Path

from hw8_planner import build_plan
from hw8_writer import build_draft


OUTPUT_DIR = Path("reports/hw10/data")
CASES_PATH = OUTPUT_DIR / "eval_cases.json"
LABELS_PATH = OUTPUT_DIR / "human_labels.csv"


QUESTIONS = [
    "How does Kafka improve coordination between independent agents?",
    "What is the role of the Planner in the pipeline?",
    "What does the Writer send after creating a draft?",
    "What does the Reviewer return to the sender?",
    "Why are correlation IDs important in the pipeline?",
    "How does Kafka decouple the Planner from the Writer?",
    "What happens when the Writer receives a task?",
    "How does the Reviewer evaluate a draft?",
    "Which topic carries Planner tasks?",
    "Which topic carries Writer drafts?",
    "Which topic carries final Reviewer results?",
    "How can a sender match a response to its request?",
    "What benefit do independent consumer groups provide?",
    "How does Kafka support reliable message delivery?",
    "Why are task IDs included in pipeline messages?",
    "What information should a Planner include in a plan?",
    "What makes a Writer draft helpful?",
    "What makes a Reviewer result useful?",
    "How does the pipeline handle work between stages?",
    "What is one limitation of the current Writer response?",
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cases = []
    for number, question in enumerate(QUESTIONS, start=1):
        plan = build_plan(question)
        draft = build_draft(question, plan)
        cases.append(
            {
                "case_id": f"writer-{number:03d}",
                "correlation_id": str(uuid.uuid4()),
                "question": question,
                "writer_draft": draft,
                "source": "hw8_writer.build_draft",
            }
        )

    CASES_PATH.write_text(
        json.dumps(cases, indent=2),
        encoding="utf-8",
    )

    with LABELS_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["case_id", "human_helpfulness_label", "human_note"],
        )
        writer.writeheader()
        for case in cases:
            writer.writerow(
                {
                    "case_id": case["case_id"],
                    "human_helpfulness_label": "",
                    "human_note": "",
                }
            )

    print(f"Created {len(cases)} cases at {CASES_PATH}")
    print(f"Created blank human-label template at {LABELS_PATH}")
    print("Assign labels manually from 1 to 5 before running the judge.")


if __name__ == "__main__":
    main()
