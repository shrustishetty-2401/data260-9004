import json
import os

import httpx

from tool_runner import execute_tool


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "qwen3:8b"

BLOCKED_TERMS = {
    "delete",
    "drop",
    "password",
    "secret",
    "credential",
    "token",
}


def safety_blocked(user_input):
    text = user_input.lower()
    return any(term in text for term in BLOCKED_TERMS)


class OllamaModel:
    def __init__(self, model=OLLAMA_MODEL):
        self.model = model

    def respond(self, messages):
        response = httpx.post(
            OLLAMA_URL,
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "format": "json",
            },
            timeout=60,
        )

        response.raise_for_status()
        payload = response.json()

        return json.loads(
            payload["message"]["content"]
        )


class MockModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.position = 0

    def respond(self, messages):
        if self.position >= len(self.responses):
            return {
                "final": "Mock model stopped",
            }

        response = self.responses[self.position]
        self.position += 1
        return response


def write_log(record, log_path=None):
    if log_path is None:
        log_path = os.path.expanduser(
            "~/data260-9004/reports/hw05/raw/agent_runs.jsonl"
        )

    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as file:
        file.write(
            json.dumps(record, default=str)
            + "\n"
        )


def run_agent(
    user_input,
    model=None,
    max_steps=3,
    log_path=None,
):
    if model is None:
        model = OllamaModel()

    if safety_blocked(user_input):
        result = {
            "final": "Request blocked by domain safety policy.",
            "stop_reason": "safety_block",
        }

        write_log(
            {
                "user_input": user_input,
                "steps": [],
                "final": result["final"],
                "stop_reason": result["stop_reason"],
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
                "vulnerability_detail, "
                "vulnerability_aggregate. "
                "Return JSON with either "
                "{tool, inputs} or {final}."
            ),
        },
        {
            "role": "user",
            "content": user_input,
        },
    ]

    steps = []

    for step_number in range(1, max_steps + 1):
        response = model.respond(messages)

        if "final" in response:
            result = {
                "final": response["final"],
                "stop_reason": "model_finished",
            }

            write_log(
                {
                    "user_input": user_input,
                    "steps": steps,
                    "final": result["final"],
                    "stop_reason": result["stop_reason"],
                },
                log_path,
            )

            return result

        tool_name = response.get("tool")
        inputs = response.get("inputs", {})

        if tool_name not in {
            "search_vulnerabilities",
            "vulnerability_detail",
            "vulnerability_aggregate",
        }:
            result = {
                "final": "The requested tool is not allowed.",
                "stop_reason": "tool_block",
            }

            write_log(
                {
                    "user_input": user_input,
                    "steps": steps,
                    "final": result["final"],
                    "stop_reason": result["stop_reason"],
                },
                log_path,
            )

            return result

        tool_result = execute_tool(
            tool_name,
            inputs,
        )

        step_record = {
            "step": step_number,
            "tool": tool_name,
            "input": inputs,
            "result": json.loads(tool_result),
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
                "content": tool_result,
            }
        )

    result = {
    "final": "Maximum tool steps reached.",
    "stop_reason": "max_steps",
    "steps": steps,
}

    write_log(
        {
            "user_input": user_input,
            "steps": steps,
            "final": result["final"],
            "stop_reason": result["stop_reason"],
        },
        log_path,
    )

    return result


def run_offline_tests():
    blocked = run_agent(
        "Delete all vulnerability records",
        model=MockModel([]),
    )

    assert blocked["stop_reason"] == "safety_block"
    print("PASS safety_block")

    limited = run_agent(
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
                    "tool": "vulnerability_detail",
                    "inputs": {
                        "vulnerability_id": 10002,
                    },
                },
            ]
        ),
        max_steps=2,
    )

    assert limited["stop_reason"] == "max_steps"
    assert len(limited["steps"]) == 2
    print("PASS max_steps")

    print("2/2 agent tests passed")


if __name__ == "__main__":
    run_offline_tests()