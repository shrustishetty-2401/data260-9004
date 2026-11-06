import os
import time
import uuid
from datetime import datetime, timezone
from typing import Callable

import numpy as np
import redis
from redis.commands.search.field import TagField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer


PREFIX = "s9004"
INDEX_NAME = f"{PREFIX}:semantic:index"
ENTRY_PREFIX = f"{PREFIX}:semantic:entry:"
EMBEDDING_DIMENSION = 384


class SemanticResponseCache:
    def __init__(
        self,
        threshold: float = 0.85,
        redis_url: str | None = None,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.threshold = threshold
        self.redis_client = redis.Redis.from_url(
            redis_url
            or os.getenv(
                "SEMANTIC_REDIS_URL",
                "redis://localhost:6381/0",
            ),
            decode_responses=False,
        )

        self.model = SentenceTransformer(model_name)
        self._ensure_index()

    def _ensure_index(self):
        try:
            self.redis_client.ft(INDEX_NAME).info()
            return
        except redis.exceptions.ResponseError:
            pass

        schema = [
            TextField("query"),
            TextField("answer"),
            TagField("data_version"),
            VectorField(
                "embedding",
                "FLAT",
                {
                    "TYPE": "FLOAT32",
                    "DIM": EMBEDDING_DIMENSION,
                    "DISTANCE_METRIC": "COSINE",
                },
            ),
        ]

        definition = IndexDefinition(
            prefix=[ENTRY_PREFIX],
            index_type=IndexType.HASH,
        )

        try:
            self.redis_client.ft(INDEX_NAME).create_index(
                schema,
                definition=definition,
            )
        except redis.exceptions.ResponseError as error:
            if "Index already exists" not in str(error):
                raise

    def embed(self, query: str) -> np.ndarray:
        vector = self.model.encode(
            query,
            normalize_embeddings=True,
        )

        return np.asarray(
            vector,
            dtype=np.float32,
        )

    def _entry_key(self, entry_id: str) -> str:
        return f"{ENTRY_PREFIX}{entry_id}"

    def _decode(self, value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")

        return str(value)

    def _escape_tag_value(self, value: str) -> str:
        special_characters = set(",.<>{}[]\"'\\:;!@#$%^&*()-+=~|")

        escaped_value = []

        for character in value:
            if character in special_characters:
                escaped_value.append("\\")

            escaped_value.append(character)

        return "".join(escaped_value)

    def _search(
        self,
        vector: np.ndarray,
        data_version: str,
    ):
        safe_version = self._escape_tag_value(
            data_version,
        )

        search_query = (
            Query(
                f"@data_version:{{{safe_version}}}"
                "=>[KNN 1 @embedding $query_vector "
                "AS vector_score]"
            )
            .sort_by("vector_score")
            .return_fields(
                "query",
                "answer",
                "data_version",
                "vector_score",
            )
            .paging(0, 1)
            .dialect(2)
        )

        result = self.redis_client.ft(INDEX_NAME).search(
            search_query,
            query_params={
                "query_vector": vector.tobytes(),
            },
        )

        if not result.docs:
            return None

        document = result.docs[0]

        stored_version = self._decode(
            getattr(
                document,
                "data_version",
                "",
            ),
        )

        if stored_version != data_version:
            return None

        distance = float(
            self._decode(
                getattr(
                    document,
                    "vector_score",
                    "1",
                ),
            ),
        )

        similarity = 1.0 - distance

        return {
            "query": self._decode(
                getattr(
                    document,
                    "query",
                    "",
                ),
            ),
            "answer": self._decode(
                getattr(
                    document,
                    "answer",
                    "",
                ),
            ),
            "similarity": similarity,
            "data_version": stored_version,
        }

    def get_or_compute(
        self,
        query: str,
        answer_function: Callable[[str], str],
        data_version: str = "v1",
    ) -> dict:
        started_at = time.perf_counter()

        vector = self.embed(query)

        match = self._search(
            vector,
            data_version,
        )

        if match is not None and match["similarity"] >= self.threshold:
            latency_ms = (time.perf_counter() - started_at) * 1000

            print(
                f"[CACHE] HIT similarity="
                f"{match['similarity']:.4f} "
                f"latency_ms={latency_ms:.2f}",
                flush=True,
            )

            return {
                "answer": match["answer"],
                "is_cached": True,
                "similarity": match["similarity"],
                "latency_ms": latency_ms,
                "data_version": data_version,
            }

        print(
            "[CACHE] MISS",
            flush=True,
        )

        answer = answer_function(query)
        entry_id = str(uuid.uuid4())

        self.redis_client.hset(
            self._entry_key(entry_id),
            mapping={
                "query": query,
                "answer": answer,
                "data_version": data_version,
                "created_at": datetime.now(
                    timezone.utc,
                ).isoformat(),
                "embedding": vector.tobytes(),
            },
        )

        latency_ms = (time.perf_counter() - started_at) * 1000

        return {
            "answer": answer,
            "is_cached": False,
            "similarity": (match["similarity"] if match is not None else None),
            "latency_ms": latency_ms,
            "data_version": data_version,
        }

    def invalidate_version(
        self,
        data_version: str,
    ) -> int:
        deleted = 0
        cursor = 0

        while True:
            cursor, keys = self.redis_client.scan(
                cursor=cursor,
                match=f"{ENTRY_PREFIX}*",
                count=100,
            )

            for key in keys:
                stored_version = self.redis_client.hget(
                    key,
                    "data_version",
                )

                if (
                    self._decode(
                        stored_version,
                    )
                    == data_version
                ):
                    deleted += int(
                        self.redis_client.delete(key),
                    )

            if cursor == 0:
                break

        print(
            f"[CACHE] Invalidated version={data_version} entries={deleted}",
            flush=True,
        )

        return deleted
