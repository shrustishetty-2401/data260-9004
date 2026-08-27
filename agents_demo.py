import argparse
import json

from ollama import chat


MODEL = "qwen3:8b"

PLANNER_SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3
        },
        "summary": {"type": "string"}
    },
    "required": ["tags", "summary"],
    "additionalProperties": False
}

REVIEWER_SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3
        },
        "summary": {"type": "string"},
        "changed": {"type": "boolean"},
        "explanation": {"type": "string"}
    },
    "required": ["tags", "summary", "changed", "explanation"],
    "additionalProperties": False
}


def ask_agent(system_message, user_message, schema, temperature):
    response = chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        format=schema,
        options={"temperature": temperature},
        think=False
    )

    return json.loads(response.message.content)


def run_planner(title, content, temperature):
    system_message = (
        "You are the Planner agent. Analyze only the supplied title and content. "
        "Create exactly three topical tags and a one-sentence summary of at most "
        "25 words. Derive everything from the input."
    )

    user_message = (
        f"Title: {title}\n"
        f"Content: {content}\n"
        "Return exactly three topical tags and a summary."
    )

    return ask_agent(
        system_message,
        user_message,
        PLANNER_SCHEMA,
        temperature
    )


def run_reviewer(title, content, planner_output, temperature):
    system_message = (
        "You are the Reviewer agent. Check whether the Planner produced exactly "
        "three distinct topical tags and a one-sentence summary of at most 25 "
        "words. Correct any problems. State whether you changed anything."
    )

    user_message = (
        f"Original title: {title}\n"
        f"Original content: {content}\n"
        f"Planner output: {json.dumps(planner_output)}"
    )

    return ask_agent(
        system_message,
        user_message,
        REVIEWER_SCHEMA,
        temperature
    )


def finalize(reviewer_output):
    tags = [tag.strip() for tag in reviewer_output["tags"]]
    summary = reviewer_output["summary"].strip()

    if len(tags) != 3:
        raise ValueError("Final output must contain exactly three tags.")

    if len({tag.lower() for tag in tags}) != 3:
        raise ValueError("Final tags must be distinct.")

    words = summary.split()

    if len(words) > 25:
        summary = " ".join(words[:25])

    return {
        "tags": tags,
        "summary": summary
    }


def run_pipeline(title, content, temperature):
    planner_output = run_planner(title, content, temperature)

    print("\nPlanner output:")
    print(json.dumps(planner_output, indent=2))

    reviewer_output = run_reviewer(
        title,
        content,
        planner_output,
        temperature
    )

    print("\nReviewer output:")
    print(json.dumps(reviewer_output, indent=2))

    final_output = finalize(reviewer_output)

    print("\nFinalized output:")
    print(json.dumps(final_output, indent=2))

    print("\nPublish output JSON:")
    print(json.dumps(final_output))

    return final_output


def main():
    parser = argparse.ArgumentParser(
        description="Generate three tags and a short summary."
    )

    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--temperature", type=float, default=0.0)

    args = parser.parse_args()

    run_pipeline(
        args.title,
        args.content,
        args.temperature
    )


if __name__ == "__main__":
    main()