from hw9_view_cache import VulnerabilityViewCache


ENTITY_ID = "hw9-test-vulnerability-001"

entities = {
    ENTITY_ID: {
        "entity_id": ENTITY_ID,
        "vulnerability_code": "HW9-COUNTER-001",
        "view_count": 0,
    }
}

cache = VulnerabilityViewCache(
    entities,
    prefix="s9004",
)

cache.reset_vulnerability_views(ENTITY_ID)

print("=== Testing Counter ===")

for access_number in range(1, 26):
    total = cache.increment_vulnerability_views(
        ENTITY_ID,
    )

    print(
        f"Access #{access_number}: Total = {total}",
        flush=True,
    )

print(
    f"Final database view_count: {entities[ENTITY_ID]['view_count']}",
    flush=True,
)

print(
    f"Redis key: s9004:views:vulnerability:{ENTITY_ID}",
    flush=True,
)
