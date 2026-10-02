import json

from domain_mcp_server import (
    search_vulnerabilities,
    vulnerability_aggregate,
    vulnerability_detail,
)


TOOLS = {
    "search_vulnerabilities": search_vulnerabilities,
    "vulnerability_detail": vulnerability_detail,
    "vulnerability_aggregate": vulnerability_aggregate,
}


BLOCKED_TERMS = {
    "delete",
    "drop",
    "password",
    "secret",
    "credential",
    "token",
}


def error_response(message):
    return json.dumps(
        {
            "ok": False,
            "data": None,
            "error": message,
        }
    )


def execute_tool(name, inputs):
    if name not in TOOLS:
        return error_response("unknown tool")

    if not isinstance(inputs, dict):
        return error_response("inputs must be an object")

    input_text = json.dumps(inputs).lower()

    if any(term in input_text for term in BLOCKED_TERMS):
        return error_response(
            "Blocked by domain safety rule"
        )

    try:
        if name == "search_vulnerabilities":
            result = TOOLS[name](
                query=inputs.get("query", ""),
                limit=inputs.get("limit", 10),
            )

        elif name == "vulnerability_detail":
            result = TOOLS[name](
                vulnerability_id=inputs.get(
                    "vulnerability_id",
                    0,
                )
            )

        else:
            if inputs:
                result = {
                    "ok": False,
                    "data": None,
                    "error": "aggregate accepts no inputs",
                }
            else:
                result = TOOLS[name]()

        return json.dumps(result, default=str)

    except Exception as error:
        return error_response(str(error))


def run_offline_tests():
    tests = [
        (
            "valid_search",
            "search_vulnerabilities",
            {"query": "Seeded", "limit": 1},
            True,
        ),
        (
            "invalid_search",
            "search_vulnerabilities",
            {"query": ""},
            False,
        ),
        (
            "valid_detail",
            "vulnerability_detail",
            {"vulnerability_id": 10002},
            True,
        ),
        (
            "invalid_detail",
            "vulnerability_detail",
            {"vulnerability_id": 0},
            False,
        ),
        (
            "valid_aggregate",
            "vulnerability_aggregate",
            {},
            True,
        ),
        (
            "invalid_aggregate",
            "vulnerability_aggregate",
            {"unexpected": "value"},
            False,
        ),
    ]

    passed = 0

    for name, tool_name, inputs, expected_ok in tests:
        output = json.loads(
            execute_tool(tool_name, inputs)
        )

        if output["ok"] == expected_ok:
            print(f"PASS {name}")
            passed += 1
        else:
            print(f"FAIL {name}")
            print(output)

    blocked_output = json.loads(
        execute_tool(
            "search_vulnerabilities",
            {"query": "delete"},
        )
    )

    assert blocked_output["ok"] is False
    assert blocked_output["error"] == (
        "Blocked by domain safety rule"
    )

    print("PASS safety_rule")
    passed += 1

    print(f"{passed}/{len(tests) + 1} tool tests passed")


if __name__ == "__main__":
    run_offline_tests()