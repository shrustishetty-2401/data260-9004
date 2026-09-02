import json
from typing import Annotated, Any, Dict, TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    field_validator,
)

from src.model_client import complete


class AgentState(TypedDict, total=False):
    title: str
    content: str
    email: str
    strict: bool
    task: str
    llm: Any
    planner_proposal: Dict[str, Any]
    reviewer_feedback: Dict[str, Any]
    validation_error: str
    final_output: Dict[str, Any]
    turn_count: int


Tag = Annotated[str, Field(min_length=3, max_length=30)]


class PlannerOutput(BaseModel):
    tags: list[Tag] = Field(min_length=3, max_length=3)
    summary: str

    @field_validator("summary")
    @classmethod
    def summary_must_be_at_most_25_words(cls, value: str) -> str:
        if len(value.split()) > 25:
            raise ValueError("Summary must contain at most 25 words.")

        return value


PLANNER_SCHEMA = {
    "type": "object",
    "properties": {
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3,
        },
        "summary": {
            "type": "string",
        },
    },
    "required": ["tags", "summary"],
    "additionalProperties": False,
}


TURN_CEILING = 2
FORCE_REVIEWER_FAILURE = False

def planner_node(state: AgentState) -> Dict[str, Any]:
    print("--- NODE: Planner ---")

    correction_message = ""

    if state.get("validation_error"):
        correction_message = (
            "\nPrevious output failed validation. Correct this problem:\n"
            f"{state['validation_error']}\n"
        )

    system_message = (
        "You are the Planner agent. Analyze only the supplied title and content. "
        "Create exactly three topical tags. Each tag must be 3 to 30 characters. "
        "Write a summary of at most 25 words. Return only valid JSON."
    )

    user_message = (
        f"Title: {state['title']}\n"
        f"Content: {state['content']}\n"
        f"{correction_message}"
        "Return exactly three tags and one summary."
    )

    response = complete(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        format=PLANNER_SCHEMA,
        options={"temperature": 0.0},
    )

    print(
        f"Planner tokens: input={response.input_tokens}, "
        f"output={response.output_tokens}, "
        f"total={response.total_tokens}"
    )

    proposal = json.loads(response.content)

    return {
        "planner_proposal": proposal,
        "validation_error": "",
    }


def reviewer_node(state: AgentState) -> Dict[str, Any]:
    print("--- NODE: Reviewer ---")
    if FORCE_REVIEWER_FAILURE:
        print("Reviewer result: forced issue for testing")

        return {
            "reviewer_feedback": {
                "valid": False,
                "message": "Temporary forced issue.",
            },
            "validation_error": "Temporary forced validation error.",
        }

    proposal = state["planner_proposal"]

    try:
        validated_output = PlannerOutput.model_validate(proposal)

        print("Reviewer result: valid")

        return {
            "reviewer_feedback": {
                "valid": True,
                "message": "Planner output passed validation.",
            },
            "final_output": validated_output.model_dump(),
            "validation_error": "",
        }

    except ValidationError as error:
        error_message = str(error)

        print("Reviewer result: invalid")
        print(error_message)

        return {
            "reviewer_feedback": {
                "valid": False,
                "message": "Planner output failed validation.",
            },
            "validation_error": error_message,
        }


def supervisor_node(state: AgentState) -> Dict[str, Any]:
    print("--- NODE: Supervisor ---")

    current_turn = state.get("turn_count", 0)
    next_turn = current_turn + 1

    print(f"Turn count: {next_turn}/{TURN_CEILING}")

    return {
        "turn_count": next_turn,
    }


def router_logic(state: AgentState) -> str:
    reviewer_feedback = state.get("reviewer_feedback", {})
    is_valid = reviewer_feedback.get("valid", False)
    turn_count = state.get("turn_count", 0)

    if is_valid:
        print("Router decision: END")
        return "end"

    if turn_count >= TURN_CEILING:
        print("Router decision: END at turn ceiling")
        return "end"

    print("Router decision: PLANNER retry")
    return "planner"


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("reviewer", reviewer_node)
    graph_builder.add_node("supervisor", supervisor_node)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "reviewer")
    graph_builder.add_edge("reviewer", "supervisor")

    graph_builder.add_conditional_edges(
        "supervisor",
        router_logic,
        {
            "planner": "planner",
            "end": END,
        },
    )

    return graph_builder.compile()

import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Run the stateful Planner/Reviewer graph."
    )

    parser.add_argument("--title", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument(
        "--email",
        default="student@sjsu.edu",
    )

    args = parser.parse_args()

    initial_state: AgentState = {
        "title": args.title,
        "content": args.content,
        "email": args.email,
        "strict": True,
        "task": "Create exactly three tags and a summary.",
        "turn_count": 0,
    }

    graph = build_graph()
    final_state: AgentState = dict(initial_state)

    print("=== Starting LangGraph run ===")

    for event in graph.stream(initial_state):
        print("\nGRAPH EVENT:")
        print(json.dumps(event, indent=2, default=str))

        for update in event.values():
            if isinstance(update, dict):
                final_state.update(update)

    print("\n=== Final state ===")
    print(json.dumps(final_state, indent=2, default=str))


if __name__ == "__main__":
    main()