import json
from pathlib import Path


BASE_DIR = Path("reports/hw09")
DATA_DIR = BASE_DIR / "data"
REFERENCE_PATH = DATA_DIR / "reference_data.json"

TRAIN_PATH = DATA_DIR / "train.jsonl"
VALIDATION_PATH = DATA_DIR / "validation.jsonl"
TEST_PATH = DATA_DIR / "test.jsonl"


REFERENCE_DATA = [
    {
        "question_id": "ref-001",
        "question": "What is the primary domain entity?",
        "answer": "The primary domain entity is Vulnerability.",
    },
    {
        "question_id": "ref-002",
        "question": "What Kafka topic receives vulnerability requests?",
        "answer": "Vulnerability requests use the s9004_vulnerability_requests topic.",
    },
    {
        "question_id": "ref-003",
        "question": "What Kafka topic receives vulnerability responses?",
        "answer": "Vulnerability responses use the s9004_vulnerability_responses topic.",
    },
    {
        "question_id": "ref-004",
        "question": "What identifies each vulnerability record?",
        "answer": "Each vulnerability record is identified by a UUID entity_id.",
    },
    {
        "question_id": "ref-005",
        "question": "What happens when the same correlation ID is delivered twice?",
        "answer": "The duplicate request is ignored and the original response is returned.",
    },
    {
        "question_id": "ref-006",
        "question": "Which topic receives Planner tasks?",
        "answer": "Planner tasks are published to the s9004_tasks topic.",
    },
    {
        "question_id": "ref-007",
        "question": "Which topic receives Writer drafts?",
        "answer": "Writer drafts are published to the s9004_drafts topic.",
    },
    {
        "question_id": "ref-008",
        "question": "How many poison-message retries are allowed?",
        "answer": "A poison message is retried three times before dead-letter handling.",
    },
    {
        "question_id": "ref-009",
        "question": "Which topic receives failed poison messages?",
        "answer": "Failed poison messages are sent to the s9004_dead_letter topic.",
    },
    {
        "question_id": "ref-010",
        "question": "How is Kafka ordering preserved for related messages?",
        "answer": "Related messages use the same Kafka key so they are routed to one partition.",
    },
    {
        "question_id": "ref-011",
        "question": "What does Redis store for the semantic cache?",
        "answer": "Redis stores the query, embedding, answer, and data-version marker.",
    },
    {
        "question_id": "ref-012",
        "question": "What similarity metric is used by the semantic cache?",
        "answer": "The semantic cache uses cosine similarity.",
    },
    {
        "question_id": "ref-013",
        "question": "What happens when the cache threshold is not met?",
        "answer": "The normal answering path runs and the new response is stored in Redis.",
    },
    {
        "question_id": "ref-014",
        "question": "Why is a data-version marker stored with cached answers?",
        "answer": "The data-version marker prevents stale answers from being reused after reference data changes.",
    },
    {
        "question_id": "ref-015",
        "question": "What threshold was selected for the vulnerability semantic cache?",
        "answer": "Threshold 0.95 was selected because it produced zero false hits.",
    },
]


TRAIN_QUESTIONS = [
    {
        "question_id": "train-001",
        "question": "What is the primary entity in the system?",
    },
    {
        "question_id": "train-002",
        "question": "Where are vulnerability requests published?",
    },
    {
        "question_id": "train-003",
        "question": "How are vulnerability records identified?",
    },
    {
        "question_id": "train-004",
        "question": "How does the system handle duplicate correlation IDs?",
    },
    {
        "question_id": "train-005",
        "question": "Where does the Writer publish drafts?",
    },
]


VALIDATION_QUESTIONS = [
    {
        "question_id": "validation-001",
        "question": "How many attempts are allowed for a poison message?",
    },
    {
        "question_id": "validation-002",
        "question": "Where are failed poison messages sent?",
    },
    {
        "question_id": "validation-003",
        "question": "How does Kafka preserve order for related messages?",
    },
    {
        "question_id": "validation-004",
        "question": "What information is kept in the semantic cache?",
    },
    {
        "question_id": "validation-005",
        "question": "Why does the cache store a data version?",
    },
]


TEST_QUESTIONS = [
    {
        "question_id": "test-001",
        "question": "Which Kafka topic receives vulnerability responses?",
    },
    {
        "question_id": "test-002",
        "question": "What does Redis keep for a cached response?",
    },
    {
        "question_id": "test-003",
        "question": "Which similarity measure does the cache use?",
    },
    {
        "question_id": "test-004",
        "question": "What threshold was selected for the cache?",
    },
    {
        "question_id": "test-005",
        "question": "What happens when a cached answer becomes stale?",
    },
]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )


DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REFERENCE_PATH.write_text(
    json.dumps(
        REFERENCE_DATA,
        indent=2,
    ),
    encoding="utf-8",
)

write_jsonl(
    TRAIN_PATH,
    TRAIN_QUESTIONS,
)

write_jsonl(
    VALIDATION_PATH,
    VALIDATION_QUESTIONS,
)

write_jsonl(
    TEST_PATH,
    TEST_QUESTIONS,
)

print(f"Saved {REFERENCE_PATH}")
print(f"Saved {TRAIN_PATH}")
print(f"Saved {VALIDATION_PATH}")
print(f"Saved {TEST_PATH}")
print()
print("Training, validation, and test files contain inputs only.")
