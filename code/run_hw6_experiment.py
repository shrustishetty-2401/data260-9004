import json
import os
import sys
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8004"

CONVERSATION = [
    (
        f"Turn {number}: Explain one important "
        "fact about package vulnerabilities."
    )
    for number in range(1, 31)
]

PROBES = [
    (
        "preference",
        "How does the user prefer explanations?",
        ["concise", "open-source"],
    ),
    (
        "recording",
        "What should be recorded for a vulnerable package?",
        ["package", "severity", "version"],
    ),
    (
        "severity",
        "Which severity levels should be prioritized first?",
        ["critical", "high"],
    ),
    (
        "transitive",
        "Why are transitive dependencies important?",
        ["indirect", "vulnerabilities"],
    ),
    (
        "no_patch",
        "What should be done when no patch exists?",
        ["replace", "workaround"],
    ),
]


def post_chat(
    user_id: str,
    session_id: str,
    message: str,
) -> dict:
    body = json.dumps(
        {
            "user_id": user_id,
            "session_id": session_id,
            "message": message,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        f"{BASE_URL}/api/chat",
        data=body,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=120,
    ) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def score_probe(
    response: str,
    expected_words: list[str],
) -> int:
    response_lower = response.lower()

    matches = sum(
        word.lower() in response_lower
        for word in expected_words
    )

    return max(
        1,
        min(
            5,
            1 + matches,
        ),
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python code/run_hw6_experiment.py 12"
        )

    short_term_n = int(sys.argv[1])

    label = os.getenv(
        "EXPERIMENT_LABEL",
        "baseline",
    )

    user_id = (
        f"hw6-experiment-{label}-{short_term_n}"
    )

    session_id = (
        f"session-{label}-{short_term_n}"
    )

    turns = []

    for message in CONVERSATION:
        result = post_chat(
            user_id,
            session_id,
            message,
        )

        turns.append(
            {
                "message": message,
                "metrics": result["metrics"],
            }
        )

        print(
            f"Completed conversation turn "
            f"{len(turns)}/30"
        )

    probes = []

    for probe_id, question, expected_words in PROBES:
        result = post_chat(
            user_id,
            session_id,
            question,
        )

        reply = result["reply"]

        score = score_probe(
            reply,
            expected_words,
        )

        probes.append(
            {
                "id": probe_id,
                "question": question,
                "score": score,
                "reply": reply,
                "metrics": result["metrics"],
            }
        )

        print(
            f"Completed probe: {probe_id}, "
            f"score={score}"
        )

    prompt_values = [
        item["metrics"]["prompt_tokens"]
        for item in turns
    ]

    latency_values = [
        item["metrics"]["latency_ms"]
        for item in turns
    ]

    probe_scores = [
        item["score"]
        for item in probes
    ]

    result = {
        "label": label,
        "short_term_n": short_term_n,
        "conversation_turns": len(turns),
        "probe_count": len(probes),
        "mean_prompt_tokens_per_turn": (
            sum(prompt_values)
            / len(prompt_values)
        ),
        "mean_latency_ms": (
            sum(latency_values)
            / len(latency_values)
        ),
        "mean_probe_quality": (
            sum(probe_scores)
            / len(probe_scores)
        ),
        "turns": turns,
        "probes": probes,
    }

    output_path = Path(
        "reports/hw06/raw"
        f"/experiment_{label}_{short_term_n}.json"
    )

    output_path.write_text(
        json.dumps(
            result,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                key: result[key]
                for key in [
                    "label",
                    "short_term_n",
                    "mean_prompt_tokens_per_turn",
                    "mean_latency_ms",
                    "mean_probe_quality",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()