from dataclasses import dataclass
from typing import Any

from ollama import chat


MODEL = "qwen3:8b"


@dataclass
class Completion:
    content: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


def complete(
    messages: list[dict[str, Any]],
    tools: Any = None,
    format: Any = None,
    options: dict[str, Any] | None = None,
) -> Completion:
    kwargs: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "think": False,
    }

    if tools is not None:
        kwargs["tools"] = tools
    if format is not None:
        kwargs["format"] = format
    if options is not None:
        kwargs["options"] = options

    response = chat(**kwargs)

    input_tokens = int(getattr(response, "prompt_eval_count", 0) or 0)
    output_tokens = int(getattr(response, "eval_count", 0) or 0)

    return Completion(
        content=response.message.content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
    )
