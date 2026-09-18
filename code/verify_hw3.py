from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent

required_files = [
    "code/api.py",
    "code/auth.py",
    "code/templates/login.html",
    "code/templates/dashboard.html",
    "reports/hw03/CORPUS_MANIFEST.json",
    "reports/hw03/questions.yaml",
    "reports/hw03/METRICS.md",
    "reports/hw03/SOURCES.md",
    "reports/hw03/report.md",
    "reports/hw03/Shetty_HW3.pdf",
    "reports/hw03/raw/retrieval/metrics.json",
]

checks = {}

for filename in required_files:
    checks[filename] = (ROOT / filename).exists()

metrics_path = ROOT / "reports/hw03/raw/retrieval/metrics.json"
try:
    json.loads(metrics_path.read_text())
    checks["metrics_json_valid"] = True
except Exception:
    checks["metrics_json_valid"] = False

verification = {
    "assignment": "DATA-260 HW3",
    "status": "passed" if all(checks.values()) else "failed",
    "checks": checks,
}

output_path = ROOT / "reports/hw03/verification.json"
output_path.write_text(json.dumps(verification, indent=2))

print(json.dumps(verification, indent=2))

if not all(checks.values()):
    sys.exit(1)