import json
import os
from typing import Any

from src.model_client import complete
from tool_runner import execute_tool


ALLOWED_TOOLS = {
    "search_vulnerabilities",
    "vulnerability_detail",
    "vulnerability_aggregate",
}

MAX_REPAIR_ATTEMPTS = 1
DEFAULT_MAX_STEPS = 6


class MockModel:
    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.position = 0

    def respond(self, messages: list[dict]) -> dict:
        if self.position >= len(self.responses):
            return {
                "final": "Mock model stopped.",
            }

        response = self.responses[self.position]
        self.position += 1
        return response


class AdapterModel:
    def respond(self, messages: list[dict]) -> dict:
        response = complete(messages=messages)

        content = response.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "")
            content = content.replace("```", "")
            content = content.strip()

        return json.loads(content)


def safety_blocked(user_input: str) -> bool:
    blocked_terms = {
        "delete all",
        "drop table",
        "destroy database",
        "password",
        "credential",
        "secret",
    }

    text = user_input.lower()

    return any(term in text for term in blocked_terms)


def write_log(
    record: dict,
    log_path: str | None = None,
) -> None:
    if log_path is None:
        log_path = os.path.expanduser("~/data260-9004/reports/hw07/RUN_LOG.txt")

    parent = os.path.dirname(log_path)

    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(
        log_path,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(
                record,
                default=str,
            )
            + "\n"
        )


def validate_tool_call(
    response: Any,
) -> tuple[bool, str]:
    if not isinstance(response, dict):
        return False, "The model response must be a JSON object."

    if "final" in response:
        if not isinstance(response["final"], str):
            return False, "The final answer must be a string."

        return True, ""

    if "tool" not in response:
        return False, ("The response must contain either 'final' or 'tool'.")

    if response["tool"] not in ALLOWED_TOOLS:
        return False, (
            f"Unknown tool: {response['tool']}. "
            f"Allowed tools are: "
            f"{sorted(ALLOWED_TOOLS)}."
        )

    if "inputs" not in response:
        return False, "A tool call must contain an 'inputs' object."

    if not isinstance(response["inputs"], dict):
        return False, "Tool inputs must be a JSON object."

    tool_name = response["tool"]
    inputs = response["inputs"]

    if tool_name == "search_vulnerabilities":
        if not isinstance(inputs.get("query"), str):
            return False, ("search_vulnerabilities requires a string 'query'.")

        if not inputs["query"].strip():
            return False, "The search query cannot be empty."

        limit = inputs.get("limit", 10)

        if not isinstance(limit, int):
            return False, "The search limit must be an integer."

        if limit < 1 or limit > 50:
            return False, "The search limit must be between 1 and 50."

    elif tool_name == "vulnerability_detail":
        vulnerability_id = inputs.get("vulnerability_id")

        if not isinstance(vulnerability_id, int):
            return False, ("vulnerability_detail requires an integer vulnerability_id.")

        if vulnerability_id < 1:
            return False, ("vulnerability_id must be a positive integer.")

    elif tool_name == "vulnerability_aggregate":
        if inputs:
            return False, ("vulnerability_aggregate accepts no inputs.")

    return True, ""


def repair_messages(
    messages: list[dict],
    problem: str,
) -> None:
    messages.append(
        {
            "role": "user",
            "content": (
                "Your previous response was invalid. "
                "Repair it once using this specific problem:\n"
                f"{problem}\n\n"
                "Return only one JSON object in exactly one "
                "of these forms:\n"
                '{"tool":"tool_name","inputs":{...}}\n'
                '{"final":"answer"}'
            ),
        }
    )


def run_agent(
    user_input: str,
    model: Any | None = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    log_path: str | None = None,
) -> dict:
    if model is None:
        model = AdapterModel()

    if safety_blocked(user_input):
        result = {
            "final": ("Request blocked by the domain safety policy."),
            "stop_reason": "safety_block",
            "tool_calls": 0,
            "steps": [],
        }

        write_log(
            {
                "user_input": user_input,
                **result,
            },
            log_path,
        )

        return result

    messages = [
        {
            "role": "system",
            "content": (
                "You are a read-only vulnerability database agent. "
                "Use only these tools: "
                "search_vulnerabilities, "
                "vulnerability_detail, and "
                "vulnerability_aggregate. "
                "You may make multiple tool calls. "
                "After every tool result, decide whether another "
                "tool is needed or return a final answer. "
                "Return only valid JSON using either:\n"
                '{"tool":"tool_name","inputs":{...}}\n'
                '{"final":"answer"}'
            ),
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    steps = []
    repair_count = 0

    for step_number in range(
        1,
        max_steps + 1,
    ):
        try:
            response = model.respond(messages)
        except Exception as error:
            result = {
                "final": "The model response could not be processed.",
                "stop_reason": "model_error",
                "tool_calls": len(steps),
                "steps": steps,
                "error": str(error),
            }

            write_log(
                {
                    "user_input": user_input,
                    **result,
                },
                log_path,
            )

            return result

        valid, problem = validate_tool_call(response)

        if not valid:
            if repair_count < MAX_REPAIR_ATTEMPTS:
                repair_count += 1
                repair_messages(messages, problem)
                continue

            result = {
                "final": ("The agent stopped after an invalid tool response."),
                "stop_reason": "repair_failed",
                "tool_calls": len(steps),
                "steps": steps,
                "error": problem,
            }

            write_log(
                {
                    "user_input": user_input,
                    **result,
                },
                log_path,
            )

            return result

        if "final" in response:
            result = {
                "final": response["final"],
                "stop_reason": "model_finished",
                "tool_calls": len(steps),
                "steps": steps,
            }

            write_log(
                {
                    "user_input": user_input,
                    **result,
                },
                log_path,
            )

            return result

        tool_name = response["tool"]
        inputs = response["inputs"]

        tool_result_text = execute_tool(
            tool_name,
            inputs,
        )

        try:
            tool_result = json.loads(tool_result_text)
        except json.JSONDecodeError:
            tool_result = {
                "ok": False,
                "error": "Tool returned invalid JSON.",
            }

        step_record = {
            "step": step_number,
            "tool": tool_name,
            "inputs": inputs,
            "observation": tool_result,
        }

        steps.append(step_record)

        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(response),
            }
        )

        messages.append(
            {
                "role": "tool",
                "content": tool_result_text,
            }
        )

    result = {
        "final": "Maximum tool-call budget reached.",
        "stop_reason": "budget_exhausted",
        "tool_calls": len(steps),
        "steps": steps,
    }

    write_log(
        {
            "user_input": user_input,
            **result,
        },
        log_path,
    )

    return result


def run_offline_tests() -> None:
    blocked = run_agent(
        "Delete all vulnerability records",
        model=MockModel([]),
    )

    assert blocked["stop_reason"] == "safety_block"
    print("PASS safety_block")

    multi_step = run_agent(
        "Find vulnerability information",
        model=MockModel(
            [
                {
                    "tool": "search_vulnerabilities",
                    "inputs": {
                        "query": "Seeded",
                        "limit": 1,
                    },
                },
                {
                    "tool": "vulnerability_aggregate",
                    "inputs": {},
                },
                {
                    "final": "The search and aggregate tools completed.",
                },
            ]
        ),
    )

    assert multi_step["stop_reason"] == "model_finished"
    assert multi_step["tool_calls"] == 2
    print("PASS multi_step")

    invalid_repair = run_agent(
        "Find one vulnerability",
        model=MockModel(
            [
                {
                    "tool": "unknown_tool",
                    "inputs": {},
                },
                {
                    "final": "Repair completed.",
                },
            ]
        ),
    )

    assert invalid_repair["stop_reason"] == "model_finished"
    print("PASS repair_path")

    print("3/3 agent tests passed")


if __name__ == "__main__":
    run_offline_tests()
