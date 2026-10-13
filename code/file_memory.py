import re
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AGENT_PATH = PROJECT_ROOT / "AGENT.md"
MEMORY_PATH = PROJECT_ROOT / "MEMORY.md"
ORIGINAL_MEMORY_PATH = (
    PROJECT_ROOT / "reports" / "hw06" / "MEMORY_original.md"
)


def load_agent() -> str:
    return AGENT_PATH.read_text(
        encoding="utf-8"
    )


def load_memory() -> str:
    if not MEMORY_PATH.exists():
        return ""

    return MEMORY_PATH.read_text(
        encoding="utf-8"
    )


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
        return datetime.fromisoformat(
            match.group(1).strip()
        )
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

    contradictions = []

    pairs = [
        (
            "the user prefers concise explanations",
            "the user prefers detailed explanations",
        ),
        (
            "the package status is open",
            "the package status is resolved",
        ),
        (
            "use mongodb for memory",
            "use mysql for memory",
        ),
    ]

    for left, right in pairs:
        if left in normalized and right in normalized:
            contradictions.append(
                f"Contradiction resolved: "
                f"'{left}' conflicts with '{right}'. "
                f"The newer or more specific fact must be verified."
            )

    return contradictions


def consolidate_memory() -> dict:
    facts = non_empty_memory_lines()

    if MEMORY_PATH.exists():
        ORIGINAL_MEMORY_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        ORIGINAL_MEMORY_PATH.write_text(
            MEMORY_PATH.read_text(
                encoding="utf-8"
            ),
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
                "## Contradictions Requiring Review",
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

    return {
        "before": len(facts),
        "after": len(
            non_empty_memory_lines()
        ),
        "contradictions": contradictions,
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