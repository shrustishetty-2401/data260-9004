import argparse
import json
import sys
from pathlib import Path

from src.model_client import complete


def load_agent_instructions():
    return Path("AGENT.md").read_text(encoding="utf-8")


class Conversation:
    def __init__(self):
        instructions = load_agent_instructions()

        self.history = [
            {
                "role": "system",
                "content": (
                    "Follow these project instructions exactly:\n\n"
                    f"{instructions}"
                ),
            }
        ]
        self.input_tokens = 0
        self.output_tokens = 0
        self.turn_count = 0

    def stats(self):
        serialized = json.dumps(self.history, ensure_ascii=False)

        return {
            "turn_count": self.turn_count,
            "cumulative_input_tokens": self.input_tokens,
            "cumulative_output_tokens": self.output_tokens,
            "cumulative_total_tokens": (
                self.input_tokens + self.output_tokens
            ),
            "serialized_history_length": len(serialized),
        }

    def print_stats(self):
        print("\n/stats")
        print(json.dumps(self.stats(), indent=2))

    def send(self, user_message):
        self.history.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        response = complete(messages=self.history)

        self.history.append(
            {
                "role": "assistant",
                "content": response.content,
            }
        )

        self.turn_count += 1
        self.input_tokens += response.input_tokens
        self.output_tokens += response.output_tokens

        print(
            f"\nTokens: input={response.input_tokens} "
            f"output={response.output_tokens} "
            f"total={response.total_tokens}"
        )
        print(f"\nAssistant:\n{response.content}")

        return response.content


def run_demo():
    conversation = Conversation()

    prompts = [
        (
            "Review this Python code and identify one issue:\n"
            "```python\n"
            "def divide(a, b):\n"
            "    return a / b\n"
            "```"
        ),
        "Explain why input validation matters in a web application.",
        "Give one example of a useful automated test for this project.",
        "What is the difference between a Docker image and a container?",
        "Summarize the main lesson from this five-turn conversation.",
    ]

    first_response = conversation.send(prompts[0])

    nonempty_lines = [
        line.strip()
        for line in first_response.splitlines()
        if line.strip()
    ]
    bullet_only = bool(nonempty_lines) and all(
        line.startswith("-") for line in nonempty_lines
    )

    print(
        "\nAGENT.md verification: "
        + ("PASS - code review used bullet-only output"
           if bullet_only
           else "FAIL - response was not bullet-only")
    )

    conversation.send(prompts[1])
    conversation.send(prompts[2])

    print("\n/stats after turn 3:")
    print(json.dumps(conversation.stats(), indent=2))

    conversation.send(prompts[3])
    conversation.send(prompts[4])

    print("\n/stats after turn 5:")
    print(json.dumps(conversation.stats(), indent=2))

    print("\nFinal cumulative totals:")
    print(json.dumps(conversation.stats(), indent=2))


def run_interactive():
    conversation = Conversation()

    print("Interactive client. Type /stats or /quit.")

    while True:
        try:
            user_message = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_message:
            continue

        if user_message == "/stats":
            conversation.print_stats()
            continue

        if user_message == "/quit":
            break

        conversation.send(user_message)

    print("\nCumulative totals on exit:")
    print(json.dumps(conversation.stats(), indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run the required five-turn demonstration.",
    )
    args = parser.parse_args()

    if args.demo:
        run_demo()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
