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


def execute_tool(name, inputs):
    if name not in TOOLS:
        return json.dumps(
            {
                "ok": False,
                "data": None,
                "error": "unknown tool",
            }
        )

    if not isinstance(inputs, dict):
        return json.dumps(
            {
                "ok": False,
                "data": None,
                "error": "inputs must be an object",
            }
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
        return json.dumps(
            {
                "ok": False,
                "data": None,
                "error": str(error),
            }
        )


def run_offline_tests():
    tests = [
        (
            "search_valid",
            execute_tool(
                "search_vulnerabilities",
                {
                    "query": "Seeded",
                    "limit": 2,
                },
            ),
        ),
        (
            "search_invalid",
            execute_tool(
                "search_vulnerabilities",
                {
                    "query": "",
                    "limit": 2,
                },
            ),
        ),
        (
            "detail_valid",
            execute_tool(
                "vulnerability_detail",
                {
                    "vulnerability_id": 10002,
                },
            ),
        ),
        (
            "detail_invalid",
            execute_tool(
                "vulnerability_detail",
                {
                    "vulnerability_id": 0,
                },
            ),
        ),
        (
            "aggregate_valid",
            execute_tool(
                "vulnerability_aggregate",
                {},
            ),
        ),
        (
            "aggregate_invalid",
            execute_tool(
                "vulnerability_aggregate",
                {
                    "unexpected": True,
                },
            ),
        ),
    ]

    passed = 0

    for test_name, raw_result in tests:
        result = json.loads(raw_result)

        if not isinstance(result, dict):
            raise AssertionError(
                f"{test_name} did not return an object"
            )

        if set(result) != {"ok", "data", "error"}:
            raise AssertionError(
                f"{test_name} returned the wrong envelope"
            )

        passed += 1
        print(f"PASS {test_name}")

    print(f"{passed}/{len(tests)} tests passed")


if __name__ == "__main__":
    run_offline_tests()