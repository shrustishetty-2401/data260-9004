import json
import subprocess
from pathlib import Path

from sqlalchemy import text

from database import engine


SID4 = "9004"
VERIFY_SEED = 269004
REPORT_DIR = Path("reports/hw04")
RAW_DIR = REPORT_DIR / "raw"
CORPUS_DIR = REPORT_DIR / "corpus"


def file_exists(path: str) -> bool:
    return Path(path).is_file()


def valid_json(path: Path) -> bool:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def json_length(path: Path) -> int:
    return len(
        json.loads(path.read_text(encoding="utf-8"))
    )


def database_counts() -> dict:
    with engine.connect() as connection:
        vulnerability_count = connection.execute(
            text("SELECT COUNT(*) FROM vulnerabilities")
        ).scalar_one()

        related_count = connection.execute(
            text("SELECT COUNT(*) FROM related_items")
        ).scalar_one()

    return {
        "vulnerabilities": vulnerability_count,
        "related_items": related_count,
    }


def main() -> None:
    commit_hash = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()

    counts = database_counts()

    checks = {
        "corpus_has_at_least_5_documents": len(
            list(CORPUS_DIR.iterdir())
        ) >= 5,
        "database_has_5000_vulnerabilities": (
            counts["vulnerabilities"] == 5000
        ),
        "database_has_200_related_items": (
            counts["related_items"] == 200
        ),
        "n_plus_one_raw_json_valid": valid_json(
            RAW_DIR / "n_plus_one_requests.json"
        ),
        "n_plus_one_has_180_requests": (
            json_length(
                RAW_DIR / "n_plus_one_requests.json"
            ) == 180
        ),
        "n_plus_one_metrics_valid": valid_json(
            RAW_DIR / "n_plus_one_metrics.json"
        ),
        "n_plus_one_has_6_metric_groups": (
            json_length(
                RAW_DIR / "n_plus_one_metrics.json"
            ) == 6
        ),
        "rag_results_valid": valid_json(
            RAW_DIR / "rag_results.json"
        ),
        "rag_evaluation_valid": valid_json(
            RAW_DIR / "rag_evaluation.json"
        ),
        "rag_k_sweep_valid": valid_json(
            RAW_DIR / "rag_k_sweep.json"
        ),
        "rag_printouts_present": file_exists(
            RAW_DIR / "rag_printouts.txt"
        ),
        "react_api_present": file_exists(
            "frontend/src/api.js"
        ),
        "react_app_present": file_exists(
            "frontend/src/App.jsx"
        ),
        "database_models_present": file_exists(
            "code/models.py"
        ),
        "benchmark_script_present": file_exists(
            "code/benchmark_hw4.py"
        ),
        "rag_script_present": file_exists(
            "code/rag.py"
        ),
        "run_log_present": file_exists(
            REPORT_DIR / "RUN_LOG.txt"
        ),
        "metrics_present": file_exists(
            REPORT_DIR / "METRICS.md"
        ),
        "ai_use_present": file_exists(
            REPORT_DIR / "AI_USE.md"
        ),
        "report_pdf_present": file_exists(
            REPORT_DIR / "report.pdf"
        ),
    }

    output = {
        "assignment": "DATA-260 HW4",
        "sid4": SID4,
        "commit_hash": commit_hash,
        "verify_seed": VERIFY_SEED,
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "database": "s9004_rel",
        "checks": checks,
        "status": (
            "passed"
            if all(checks.values())
            else "incomplete"
        ),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = REPORT_DIR / "verification.json"
    output_path.write_text(
        json.dumps(output, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()