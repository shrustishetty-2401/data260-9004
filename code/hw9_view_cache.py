import os
from typing import Any

import redis


class VulnerabilityViewCache:
    def __init__(
        self,
        entities: dict[str, dict[str, Any]],
        prefix: str = "s9004",
    ):
        redis_url = os.getenv(
            "REDIS_URL",
            "redis://localhost:6380/0",
        )

        self.redis_client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
        )
        self.entities = entities
        self.prefix = prefix

    def _view_key(self, entity_id: str) -> str:
        return f"{self.prefix}:views:vulnerability:{entity_id}"

    def increment_vulnerability_views(
        self,
        entity_id: str,
    ) -> int:
        key = self._view_key(entity_id)
        count = int(self.redis_client.incr(key))

        if count % 10 == 0:
            entity = self.entities.get(entity_id)

            if entity is not None:
                entity["view_count"] = count

                print(
                    f"[CACHE] Synced views to database: "
                    f"entity_id={entity_id} count={count}",
                    flush=True,
                )

        return count

    def reset_vulnerability_views(
        self,
        entity_id: str,
    ) -> None:
        self.redis_client.delete(
            self._view_key(entity_id),
        )
