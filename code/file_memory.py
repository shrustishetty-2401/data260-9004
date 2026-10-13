import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AGENT_PATH = PROJECT_ROOT / "AGENT.md"
MEMORY_PATH = PROJECT_ROOT / "MEMORY.md"
ORIGINAL_MEMORY_PATH = (
    PROJECT_ROOT / "reports" / "hw06" / "MEMORY_original.md"
)


CONTRADICTION_DECISIONS = [
    {
        "left": "the user prefers concise explanations",
        "right": "the user prefers detailed explanations",
        "decision": (
            "Retained concise explanations because the current "
            "user preference is concise technical answers."
        ),
        "incorrect_fact": (
            "The detailed-explanations fact is superseded for this project."
        ),
        "verification": (
            "Verify again if the user's preference changes."
        ),
    },
    {
        "left": "the package status is open",
        "right": "the package status is resolved",
        "decision": (
            "Retained resolved as the latest operational status."
        ),
        "incorrect_fact": (
            "The open status is treated as outdated, but this decision "
            "may be incorrect because the source facts have no timestamps."
        ),
        "verification": (
            "Verify against the current package record."
        ),
    },
    {
        "left": "use mongodb for memory",
        "right": "use mysql for memory",
        "decision": (
            "Retained MongoDB because HW6 explicitly uses MongoDB "
            "for document and conversational memory."
        ),
        "incorrect_fact": (
            "The MySQL memory instruction is incorrect for HW6, although "
            "MySQL remains part of the earlier SQL application."
        ),
        "verification": (
            "Verify against the HW6 architecture and AGENT.md."
        ),
    },
]


def load_agent() -> str:
    return AGENT_PATH.read_text(encoding="utf-8")


def load_memory() -> str:
    if not MEMORY_PATH.exists():
        return ""

    return MEMORY_PATH.read_text(encoding="utf-8")


def build_file_memory_prompt() -> str:
    return (
        "Project instructions:\n"
        f"{load_agent()}\n\n"
        "Durable memory:\n"
        f"{load_memory()}"
    )


def non_empty_memory_lines() -> list[str]:
    return [
        line.strip()
        for line in load_memory().splitlines()
        if line.strip()
        and not line.strip().startswith("#")
    ]


def get_consolidation_timestamp() -> datetime | None:
    match = re.search(
        r"Consolidated at:\s*(.+)",
        load_memory(),
    )

    if not match:
        return None

    try:
        timestamp = datetime.fromisoformat(
            match.group(1).strip()
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp
    except ValueError:
        return None


def consolidation_required() -> bool:
    lines_exceed_limit = (
        len(non_empty_memory_lines()) > 40
    )

    timestamp = get_consolidation_timestamp()

    older_than_one_day = (
        timestamp is None
        or datetime.now(timezone.utc) - timestamp
        > timedelta(hours=24)
    )

    return lines_exceed_limit or older_than_one_day


def normalize_fact(fact: str) -> str:
    fact = fact.strip()
    fact = re.sub(r"^[-*]\s*", "", fact)
    fact = re.sub(r"\s+", " ", fact)
    return fact.lower().rstrip(".")


def detect_contradictions(
    facts: list[str],
) -> list[str]:
    normalized = {
        normalize_fact(fact)
        for fact in facts
    }

    decisions = []

    for item in CONTRADICTION_DECISIONS:
        left_present = item["left"] in normalized
        right_present = item["right"] in normalized

        if left_present and right_present:
            decisions.append(
                "Contradiction decision: "
                f"'{item['left']}' conflicts with "
                f"'{item['right']}'. "
                f"Decision: {item['decision']} "
                f"Incorrect or outdated fact identified: "
                f"{item['incorrect_fact']} "
                f"Verification: {item['verification']}"
            )

    return decisions


def consolidate_memory() -> dict:
    facts = non_empty_memory_lines()
    before_count = len(facts)

    if MEMORY_PATH.exists():
        ORIGINAL_MEMORY_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        ORIGINAL_MEMORY_PATH.write_text(
            MEMORY_PATH.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    unique_facts = []
    seen = set()

    for fact in facts:
        key = normalize_fact(fact)

        if key not in seen:
            seen.add(key)
            unique_facts.append(fact)

    contradictions = detect_contradictions(
        unique_facts
    )

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    output_lines = [
        "# Consolidated Memory",
        f"Consolidated at: {timestamp}",
        "",
    ]

    output_lines.extend(
        f"- {fact}"
        for fact in unique_facts
    )

    if contradictions:
        output_lines.extend(
            [
                "",
                "## Explicit Contradiction Decisions",
            ]
        )

        output_lines.extend(
            f"- {item}"
            for item in contradictions
        )

    MEMORY_PATH.write_text(
        "\n".join(output_lines) + "\n",
        encoding="utf-8",
    )

    after_count = len(
        non_empty_memory_lines()
    )

    return {
        "before": before_count,
        "after": after_count,
        "contradictions": contradictions,
        "original_memory": str(
            ORIGINAL_MEMORY_PATH
        ),
        "consolidated_memory": str(
            MEMORY_PATH
        ),
        "consolidation_timestamp": timestamp,
    }


def memory_command(
    command: str,
    recent_conversation: str = "",
) -> dict:
    if command == "/memory":
        return {
            "command": command,
            "memory": load_memory(),
        }

    if command == "/compact":
        result = consolidate_memory()

        return {
            "command": command,
            "message": (
                f"Consolidated MEMORY.md from "
                f"{result['before']} lines to "
                f"{result['after']} lines."
            ),
            "details": result,
        }

    if command == "/dream":
        facts = [
            line.strip()
            for line in recent_conversation.splitlines()
            if line.strip()
        ]

        MEMORY_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with MEMORY_PATH.open(
            "a",
            encoding="utf-8",
        ) as file:
            for fact in facts[:3]:
                file.write(f"- {fact}\n")

        return {
            "command": command,
            "added_facts": facts[:3],
        }

    if command == "/help":
        return {
            "command": command,
            "commands": {
                "/memory": "Display file-based memory.",
                "/compact": "Consolidate MEMORY.md.",
                "/dream": "Save useful recent facts.",
                "/help": "Display available commands.",
            },
        }

    return {
        "command": command,
        "error": "Unknown memory command.",
    }