# Homework 1 Metrics

## Non-determinism results

| Metric | Temperature 0.7 | Temperature 0.0 |
|---|---:|---:|
| Successful runs | 20 | 20 |
| Distinct tag sets | 5 | 1 |
| Tags appearing in all 20 runs | None | dependency audit; package security; vulnerability management |
| Tags appearing in exactly 1 run | open-source; package upgrades; security; security auditing; software security; vulnerability scanning | None |

## Latency

| Metric | Temperature 0.7 (ms) | Temperature 0.0 (ms) |
|---|---:|---:|
| p50 | 6946.11 | 7652.65 |
| p95 | 7671.28 | 8587.59 |
| p99 | 7816.91 | 8598.61 |

## Token accounting

| Checkpoint | Turns | Input tokens | Output tokens | Total tokens | Serialized history length |
|---|---:|---:|---:|---:|---:|
| After turn 3 | 3 | 479 | 132 | 611 | 1549 |
| After turn 5 | 5 | 1129 | 213 | 1342 | 2256 |

## Interpretation

At temperature 0.7, identical inputs produced five distinct tag sets, showing run-to-run variation. At temperature 0.0, all 20 runs produced one stable tag set.

Variation can be acceptable for exploratory discovery, where alternative topical labels are useful. It is not acceptable for compliance or security classification, where identical inputs should produce repeatable labels.

Input tokens increased from turn 3 to turn 5 because prior conversation history was resent with every request. The context window eventually limits how much history can be retained.
