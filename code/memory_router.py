import hashlib
import json
import math
import os
import re
import time
from pathlib import Path
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter
from pydantic import BaseModel, Field

from mongo_database import (
    episodes_collection,
    messages_collection,
    summaries_collection,
    utc_now,
)
from src.model_client import complete


SHORT_TERM_N = int(os.getenv("SHORT_TERM_N", "12"))
SUMMARIZE_EVERY_USER_MSGS = int(
    os.getenv("SUMMARIZE_EVERY_USER_MSGS", "3")
)
EPISODE_TOP_K = int(os.getenv("EPISODE_TOP_K", "3"))
MAX_EPISODES_PER_USER = int(
    os.getenv("MAX_EPISODES_PER_USER", "10")
)

METRICS_PATH = Path("reports/hw06/raw/chat_metrics.jsonl")

SYSTEM_PRIMER = (
    "You are a helpful assistant for an open-source vulnerability "
    "tracking system. Answer clearly and accurately. Use the supplied "
    "memory when relevant, but do not invent facts."
)

router = APIRouter(tags=["memory"])


def make_json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    return value


def estimate_tokens(text: Optional[str]) -> int:
    if not text:
        return 0

    return len(re.findall(r"\S+", text))


def append_chat_metrics(record: dict) -> None:
    METRICS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with METRICS_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, default=str) + "\n")


class ChatRequest(BaseModel):
    user_id: str = Field(
        min_length=1,
        max_length=120,
    )
    session_id: Optional[str] = Field(
        default=None,
        max_length=120,
    )
    message: str = Field(
        min_length=1,
        max_length=5000,
    )


def embed_text(
    text: str,
    dimensions: int = 32,
) -> list[float]:
    vector = [0.0] * dimensions
    words = re.findall(
        r"[a-zA-Z0-9']+",
        text.lower(),
    )

    for word in words:
        digest = hashlib.sha256(
            word.encode("utf-8")
        ).digest()

        index = int.from_bytes(
            digest[:4],
            "big",
        ) % dimensions

        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    magnitude = math.sqrt(
        sum(value * value for value in vector)
    )

    if magnitude == 0:
        return vector

    return [
        value / magnitude
        for value in vector
    ]


def cosine_similarity(
    left: list[float],
    right: list[float],
) -> float:
    if not left or not right:
        return 0.0

    size = min(len(left), len(right))

    numerator = sum(
        left[index] * right[index]
        for index in range(size)
    )

    left_size = math.sqrt(
        sum(value * value for value in left[:size])
    )

    right_size = math.sqrt(
        sum(value * value for value in right[:size])
    )

    if left_size == 0 or right_size == 0:
        return 0.0

    return numerator / (left_size * right_size)


def extract_facts(message: str) -> list[str]:
    parts = [
        part.strip()
        for part in re.split(
            r"[.!?]+",
            message,
        )
        if part.strip()
    ]

    if not parts:
        parts = [message.strip()]

    facts = []

    for part in parts[:3]:
        fact = part[:240]

        if fact and fact not in facts:
            facts.append(fact)

    return facts


def store_episodes(
    user_id: str,
    session_id: Optional[str],
    message: str,
) -> None:
    facts = extract_facts(message)
    now = utc_now()
    documents = []

    for fact in facts:
        importance = (
            0.8
            if any(
                word in fact.lower()
                for word in [
                    "my",
                    "i am",
                    "i'm",
                    "always",
                    "never",
                    "prefer",
                ]
            )
            else 0.5
        )

        documents.append(
            {
                "user_id": user_id,
                "session_id": session_id,
                "fact": fact,
                "importance": importance,
                "embedding": embed_text(fact),
                "created_at": now,
            }
        )

    if not documents:
        return

    episodes_collection.insert_many(documents)

    overflow = (
        episodes_collection.count_documents(
            {"user_id": user_id}
        )
        - MAX_EPISODES_PER_USER
    )

    if overflow <= 0:
        return

    oldest = list(
        episodes_collection.find(
            {"user_id": user_id},
            {"_id": 1},
        )
        .sort("created_at", 1)
        .limit(overflow)
    )

    oldest_ids = [
        item["_id"]
        for item in oldest
    ]

    if oldest_ids:
        episodes_collection.delete_many(
            {"_id": {"$in": oldest_ids}}
        )


def get_relevant_episodes(
    user_id: str,
    message: str,
) -> list[dict]:
    query_embedding = embed_text(message)

    candidates = list(
        episodes_collection.find(
            {"user_id": user_id}
        )
    )

    ranked = []

    for episode in candidates:
        score = cosine_similarity(
            query_embedding,
            episode.get("embedding", []),
        )

        episode["similarity"] = round(score, 4)
        ranked.append(episode)

    ranked.sort(
        key=lambda item: (
            item.get("similarity", 0),
            item.get("importance", 0),
        ),
        reverse=True,
    )

    return ranked[:EPISODE_TOP_K]


def get_short_term_messages(
    user_id: str,
    session_id: Optional[str],
) -> list[dict]:
    messages = list(
        messages_collection.find(
            {
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        .sort("created_at", -1)
        .limit(SHORT_TERM_N)
    )

    messages.reverse()
    return messages


def get_latest_summary(
    user_id: str,
    session_id: Optional[str],
) -> Optional[dict]:
    return summaries_collection.find_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "scope": "session",
        },
        sort=[("created_at", -1)],
    )


def get_lifetime_summary(
    user_id: str,
) -> Optional[dict]:
    return summaries_collection.find_one(
        {
            "user_id": user_id,
            "session_id": None,
            "scope": "user",
        },
        sort=[("created_at", -1)],
    )


def build_prompt(
    user_id: str,
    session_id: Optional[str],
    current_message: str,
) -> tuple[list[dict], dict]:
    short_term = get_short_term_messages(
        user_id,
        session_id,
    )

    session_summary = get_latest_summary(
        user_id,
        session_id,
    )

    lifetime_summary = get_lifetime_summary(user_id)

    episodes = get_relevant_episodes(
        user_id,
        current_message,
    )

    context_parts = [SYSTEM_PRIMER]

    if lifetime_summary:
        context_parts.append(
            "Lifetime summary:\n"
            f"{lifetime_summary['text']}"
        )

    if session_summary:
        context_parts.append(
            "Session summary:\n"
            f"{session_summary['text']}"
        )

    if episodes:
        facts = "\n".join(
            f"- {episode['fact']}"
            for episode in episodes
        )

        context_parts.append(
            f"Episodic facts:\n{facts}"
        )

    prompt_messages = [
        {
            "role": "system",
            "content": "\n\n".join(context_parts),
        }
    ]

    for message in short_term:
        prompt_messages.append(
            {
                "role": message["role"],
                "content": message["content"],
            }
        )

    prompt_messages.append(
        {
            "role": "user",
            "content": current_message,
        }
    )

    used = {
        "short_term_count": len(short_term),
        "short_term_messages": [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in short_term
        ],
        "long_term_summary": (
            session_summary["text"]
            if session_summary
            else None
        ),
        "lifetime_summary": (
            lifetime_summary["text"]
            if lifetime_summary
            else None
        ),
        "episodic_facts": [
            {
                "fact": episode["fact"],
                "importance": episode["importance"],
                "similarity": episode["similarity"],
            }
            for episode in episodes
        ],
    }

    return prompt_messages, used


def summarize_session(
    user_id: str,
    session_id: Optional[str],
) -> None:
    messages = get_short_term_messages(
        user_id,
        session_id,
    )

    conversation = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in messages
    )

    result = complete(
        [
            {
                "role": "system",
                "content": (
                    "Summarize this conversation in concise "
                    "bullet points. Keep important user "
                    "preferences, facts, decisions, and "
                    "unresolved items."
                ),
            },
            {
                "role": "user",
                "content": conversation,
            },
        ]
    )

    summaries_collection.insert_one(
        {
            "user_id": user_id,
            "session_id": session_id,
            "scope": "session",
            "text": result.content,
            "created_at": utc_now(),
        }
    )


def summarize_lifetime(user_id: str) -> None:
    summaries = list(
        summaries_collection.find(
            {
                "user_id": user_id,
                "scope": "session",
            },
            {
                "_id": 0,
                "text": 1,
            },
        )
        .sort("created_at", -1)
        .limit(5)
    )

    if not summaries:
        return

    summary_text = "\n\n".join(
        summary["text"]
        for summary in summaries
    )

    result = complete(
        [
            {
                "role": "system",
                "content": (
                    "Create a concise lifetime memory summary "
                    "from these session summaries. Preserve "
                    "user preferences, important facts, decisions, "
                    "and unresolved items."
                ),
            },
            {
                "role": "user",
                "content": summary_text,
            },
        ]
    )

    summaries_collection.insert_one(
        {
            "user_id": user_id,
            "session_id": None,
            "scope": "user",
            "text": result.content,
            "created_at": utc_now(),
        }
    )


@router.post("/api/chat")
def chat_endpoint(payload: ChatRequest):
    started = time.perf_counter()

    messages_collection.insert_one(
        {
            "user_id": payload.user_id,
            "session_id": payload.session_id,
            "role": "user",
            "content": payload.message,
            "created_at": utc_now(),
        }
    )

    store_episodes(
        payload.user_id,
        payload.session_id,
        payload.message,
    )

    prompt_messages, used = build_prompt(
        payload.user_id,
        payload.session_id,
        payload.message,
    )

    result = complete(prompt_messages)

    messages_collection.insert_one(
        {
            "user_id": payload.user_id,
            "session_id": payload.session_id,
            "role": "assistant",
            "content": result.content,
            "created_at": utc_now(),
        }
    )

    user_message_count = messages_collection.count_documents(
        {
            "user_id": payload.user_id,
            "session_id": payload.session_id,
            "role": "user",
        }
    )

    summary_created = False

    if (
        user_message_count
        % SUMMARIZE_EVERY_USER_MSGS
        == 0
    ):
        summarize_session(
            payload.user_id,
            payload.session_id,
        )

        summarize_lifetime(
            payload.user_id,
        )

        summary_created = True

    latency_ms = round(
        (time.perf_counter() - started) * 1000,
        2,
    )

    short_term_text = "\n".join(
        item["content"]
        for item in used["short_term_messages"]
    )

    episodic_text = "\n".join(
        item["fact"]
        for item in used["episodic_facts"]
    )

    append_chat_metrics(
        {
            "timestamp": utc_now().isoformat(),
            "user_id": payload.user_id,
            "session_id": payload.session_id,
            "prompt_tokens": result.input_tokens,
            "completion_tokens": result.output_tokens,
            "total_tokens": result.total_tokens,
            "system_primer_tokens": estimate_tokens(
                SYSTEM_PRIMER
            ),
            "long_term_summary_tokens": (
                estimate_tokens(
                    used["long_term_summary"]
                )
                + estimate_tokens(
                    used["lifetime_summary"]
                )
            ),
            "short_term_window_tokens": estimate_tokens(
                short_term_text
            ),
            "episodic_facts_tokens": estimate_tokens(
                episodic_text
            ),
            "latency_ms": latency_ms,
            "summary_created": summary_created,
        }
    )

    return {
        "reply": result.content,
        "memory_used": used,
        "metrics": {
            "prompt_tokens": result.input_tokens,
            "completion_tokens": result.output_tokens,
            "total_tokens": result.total_tokens,
            "latency_ms": latency_ms,
            "summary_created": summary_created,
        },
    }


@router.get("/api/memory/{user_id}")
def get_memory(user_id: str):
    messages = list(
        messages_collection.find(
            {"user_id": user_id}
        )
        .sort("created_at", -1)
        .limit(16)
    )

    session_summary = summaries_collection.find_one(
        {
            "user_id": user_id,
            "scope": "session",
        },
        sort=[("created_at", -1)],
    )

    lifetime_summary = get_lifetime_summary(user_id)

    episodes = list(
        episodes_collection.find(
            {"user_id": user_id}
        )
        .sort("created_at", -1)
        .limit(20)
    )

    response = {
        "messages": messages,
        "latest_session_summary": session_summary,
        "latest_lifetime_summary": lifetime_summary,
        "episodic_facts": episodes,
    }

    return make_json_safe(response)


@router.get("/api/aggregate/{user_id}")
def get_aggregate(user_id: str):
    daily_counts = list(
        messages_collection.aggregate(
            [
                {
                    "$match": {
                        "user_id": user_id
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {
                                "format": "%Y-%m-%d",
                                "date": "$created_at",
                            }
                        },
                        "count": {
                            "$sum": 1
                        },
                    }
                },
                {
                    "$sort": {
                        "_id": 1
                    }
                },
            ]
        )
    )

    recent_summaries = list(
        summaries_collection.find(
            {
                "user_id": user_id
            },
            {
                "_id": 0
            },
        )
        .sort("created_at", -1)
        .limit(5)
    )

    response = {
        "daily_message_counts": daily_counts,
        "recent_summaries": recent_summaries,
    }

    return make_json_safe(response)