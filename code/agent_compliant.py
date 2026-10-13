from datetime import datetime, timezone


def summarize_memory_state(
    message_count: int,
    source: str,
) -> dict[str, str | int]:
    if message_count < 0:
        raise ValueError(
            "message_count must not be negative"
        )

    if not source.strip():
        raise ValueError(
            "source must not be blank"
        )

    return {
        "message_count": message_count,
        "source": source.strip(),
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }