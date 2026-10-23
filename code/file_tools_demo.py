import json
from pathlib import Path


SAFE_ROOT = Path("reports/hw07/raw").resolve()


def safe_path(relative_path: str) -> Path:
    candidate = (SAFE_ROOT / relative_path).resolve()

    if candidate != SAFE_ROOT and SAFE_ROOT not in candidate.parents:
        raise PermissionError("Blocked: path is outside the approved HW7 directory.")

    return candidate


def list_files():
    return sorted(
        str(path.relative_to(SAFE_ROOT))
        for path in SAFE_ROOT.rglob("*")
        if path.is_file()
    )


def read_file(relative_path: str) -> str:
    path = safe_path(relative_path)

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {relative_path}")

    return path.read_text(encoding="utf-8")


def write_file(
    relative_path: str,
    content: str,
    confirmed: bool = False,
):
    if not confirmed:
        return {
            "ok": False,
            "error": (
                "Write blocked. Explicit confirmation is required "
                "before modifying a file."
            ),
        }

    path = safe_path(relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return {
        "ok": True,
        "path": str(path),
        "bytes_written": len(content.encode("utf-8")),
    }


def main():
    results = {
        "list_files": list_files()[:20],
        "read_test": None,
        "write_without_confirmation": None,
        "path_traversal_test": None,
    }

    results["read_test"] = read_file("prompt_injection_results.json")[:200]

    results["write_without_confirmation"] = write_file(
        "safety_test.txt",
        "This write must be blocked.",
        confirmed=False,
    )

    try:
        safe_path("../../.env")
        results["path_traversal_test"] = {
            "blocked": False,
            "error": "Path traversal was not blocked.",
        }
    except PermissionError as error:
        results["path_traversal_test"] = {
            "blocked": True,
            "error": str(error),
        }

    output_path = SAFE_ROOT / "file_tools_results.json"
    output_path.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(results, indent=2))
    print(f"Saved results to {output_path}")


if __name__ == "__main__":
    main()
