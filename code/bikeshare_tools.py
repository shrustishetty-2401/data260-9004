import ast
import csv
import hashlib
import io
import operator
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


RAW_DIR = Path("reports/hw07/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def success(data):
    return {
        "ok": True,
        "data": data,
        "error": None,
    }


def failure(message):
    return {
        "ok": False,
        "data": None,
        "error": message,
    }


def csv_sql(csv_text: str):
    """Analyze an uploaded bike-share CSV."""

    if not csv_text.strip():
        return failure("CSV input is empty")

    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)

    if not rows:
        return failure("CSV contains no data rows")

    required_columns = {"duration_min", "member_type"}
    missing = required_columns - set(reader.fieldnames or [])

    if missing:
        return failure(f"CSV is missing required columns: {sorted(missing)}")

    durations = []
    member_counts = Counter()
    member_minutes = Counter()

    for row in rows:
        try:
            duration = float(row["duration_min"])
        except (TypeError, ValueError):
            continue

        member_type = row["member_type"].strip().lower()

        if member_type not in {"member", "casual"}:
            continue

        durations.append(duration)
        member_counts[member_type] += 1
        member_minutes[member_type] += duration

    if not durations:
        return failure("CSV has no valid duration/member rows")

    weekly_summary = []

    for member_type in ("member", "casual"):
        count = member_counts[member_type]
        total_minutes = member_minutes[member_type]

        weekly_summary.append(
            {
                "member_type": member_type,
                "rides": count,
                "total_minutes": round(total_minutes, 2),
                "average_minutes": round(total_minutes / count, 2) if count else 0,
            }
        )

    return success(
        {
            "row_count": len(rows),
            "valid_trip_count": len(durations),
            "minimum_duration": round(min(durations), 2),
            "maximum_duration": round(max(durations), 2),
            "average_duration": round(
                sum(durations) / len(durations),
                2,
            ),
            "weekly_summary": weekly_summary,
        }
    )


def policy_retriever(pricing_url: str):
    """Retrieve pricing text and save a local pricing snapshot."""

    # Converts copied Markdown links into a normal URL.
    markdown_match = re.fullmatch(
        r"\[(https?://[^\]]+)\]\((https?://[^)]+)\)",
        pricing_url.strip(),
    )

    if markdown_match:
        pricing_url = markdown_match.group(2)

    if not pricing_url.startswith(("http://", "https://")):
        return failure("Pricing URL must begin with http:// or https://")

    try:
        request = urllib.request.Request(
            pricing_url,
            headers={"User-Agent": "DATA260-HW7"},
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            raw_bytes = response.read()

        raw_text = raw_bytes.decode("utf-8", errors="ignore")

        clean_text = re.sub(
            r"<script.*?</script>",
            " ",
            raw_text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        clean_text = re.sub(
            r"<style.*?</style>",
            " ",
            clean_text,
            flags=re.IGNORECASE | re.DOTALL,
        )

        clean_text = re.sub(r"<[^>]+>", " ", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        snapshot_hash = hashlib.sha256(raw_bytes).hexdigest()
        timestamp = datetime.now(timezone.utc).isoformat()

        snapshot_path = RAW_DIR / "pricing_snapshot.txt"
        hash_path = RAW_DIR / "pricing_snapshot.sha256"

        snapshot_path.write_text(clean_text, encoding="utf-8")
        hash_path.write_text(snapshot_hash, encoding="utf-8")

        return success(
            {
                "source_url": pricing_url,
                "retrieved_at": timestamp,
                "sha256": snapshot_hash,
                "snapshot_file": str(snapshot_path),
                "hash_file": str(hash_path),
                "text_preview": clean_text[:2000],
            }
        )

    except Exception as error:
        return failure(f"Could not retrieve pricing policy: {error}")


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluate_math(node):
    if isinstance(node, ast.Expression):
        return _evaluate_math(node.body)

    if isinstance(node, ast.Constant) and isinstance(
        node.value,
        (int, float),
    ):
        return node.value

    if isinstance(node, ast.UnaryOp):
        operation = _ALLOWED_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unary operator is not allowed")

        return operation(_evaluate_math(node.operand))

    if isinstance(node, ast.BinOp):
        operation = _ALLOWED_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Binary operator is not allowed")

        left = _evaluate_math(node.left)
        right = _evaluate_math(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent is too large")

        return operation(left, right)

    raise ValueError("Only basic arithmetic is allowed")


def calculator(expression: str):
    """Safely evaluate basic arithmetic without eval()."""

    if not expression.strip():
        return failure("Expression is empty")

    if len(expression) > 100:
        return failure("Expression is too long")

    if not re.fullmatch(
        r"[0-9+\-*/().\s]+",
        expression,
    ):
        return failure("Expression contains unsupported characters")

    try:
        tree = ast.parse(expression, mode="eval")
        value = _evaluate_math(tree)

        if not isinstance(value, (int, float)):
            return failure("Expression did not produce a number")

        return success(
            {
                "expression": expression,
                "result": round(float(value), 2),
            }
        )

    except Exception as error:
        return failure(f"Invalid calculation: {error}")


TOOLS = {
    "csv_sql": csv_sql,
    "policy_retriever": policy_retriever,
    "calculator": calculator,
}


def execute_bikeshare_tool(name: str, inputs: dict):
    if name not in TOOLS:
        return failure("Unknown bike-share tool")

    if not isinstance(inputs, dict):
        return failure("Tool inputs must be an object")

    try:
        return TOOLS[name](**inputs)

    except TypeError as error:
        return failure(f"Invalid tool arguments: {error}")

    except Exception as error:
        return failure(str(error))
