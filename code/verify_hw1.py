import json
from pathlib import Path


required_files = [
    "DOMAIN_SCHEMA.md",
    "code/web_application/index.html",
    "code/web_application/script.js",
    "code/Dockerfile",
    "code/agents_demo.py",
    "AGENT.md",
    "code/hw1_client.py",
    "src/model_client.py",
    "reports/hw01/cases/nondeterminism_input.json",
    "reports/hw01/raw/nondeterminism_runs.json",
    "reports/hw01/raw/nondeterminism_summary.json",
    "reports/hw01/METRICS.md",
    "reports/hw01/AI_USE.md",
    "README.md",
]

checks = {
    path: Path(path).is_file()
    for path in required_files
}

try:
    input_data = json.loads(
        Path(
            "reports/hw01/cases/nondeterminism_input.json"
        ).read_text()
    )
    checks["fixed_input_is_valid_json"] = (
        "title" in input_data and "content" in input_data
    )

    runs = json.loads(
        Path(
            "reports/hw01/raw/nondeterminism_runs.json"
        ).read_text()
    )
    checks["exactly_40_runs"] = len(runs) == 40
    checks["all_runs_successful"] = all(
        row.get("status") == "ok" for row in runs
    )

    summary = json.loads(
        Path(
            "reports/hw01/raw/nondeterminism_summary.json"
        ).read_text()
    )
    checks["summary_has_both_temperatures"] = (
        "0.7" in summary and "0.0" in summary
    )

    html = Path("code/web_application/index.html").read_text()
    javascript = Path("code/web_application/script.js").read_text()
    checks["html_contains_form"] = "<form" in html
    checks["html_links_javascript"] = "script.js" in html
    checks["javascript_uses_arrow_function"] = "=>" in javascript

except Exception as exc:
    checks["verification_error"] = str(exc)

result = {
    "passed": all(checks.values()),
    "checks": checks,
}

print(json.dumps(result, indent=2))
