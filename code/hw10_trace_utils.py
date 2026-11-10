import json
import os
from datetime import datetime, timezone
from pathlib import Path


PREFIX = os.getenv("PREFIX", "s9004")
TRACE_PATH = Path("reports/hw10/raw/traces.jsonl")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_span(
    trace_id,
    stage,
    start_time,
    end_time,
    status="success",
    error=None,
    metadata=None,
):
    TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
    span = {
        "trace_id": trace_id,
        "stage": stage,
        "start_time": start_time,
        "end_time": end_time,
        "status": status,
        "error": error,
        "metadata": metadata or {},
    }

    with TRACE_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(span) + "\n")

    return span
