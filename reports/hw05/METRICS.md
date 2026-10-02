# HW5 Metrics

## Retry Benchmark

The retry benchmark used `VERIFY_SEED=269004` and three rejection rates. Each rate was tested with 50 requests, producing 150 raw JSONL records.

| Injected failure rate | Requests | Success rate | Mean latency (ms) | P99 latency (ms) | Mean attempts |
|---:|---:|---:|---:|---:|---:|
| 0% | 50 | 100% | 0.00006 | 0.002 | 1.00 |
| 20% | 50 | 100% | 0.00806 | 0.132 | 1.14 |
| 50% | 50 | 100% | 0.0166 | 0.058 | 1.52 |

The benchmark records:

- Success count
- Failure count
- Success rate
- Mean retry attempts
- P99 elapsed time
- Total request count

The complete raw records are stored in `raw/retry_records.jsonl`.

## Agent Metrics

## Agent Metrics

The local Ollama model was `qwen3:8b`.

| Scenario | Steps | Tool-call count | Stop reason |
|---|---:|---:|---|
| Vulnerability search | 3 | 3 | Maximum step limit |
| Vulnerability detail | 3 | 3 | Maximum step limit |
| Vulnerability aggregate | 0 | 0 | Model finished |
| Destructive request | 0 | 0 | Safety block |

The agent metrics record the stop reason, number of tool steps, elapsed time, and scenario result. Detailed tool inputs and outputs are stored in `raw/agent_runs.jsonl`.

## Offline Tests

The single `execute_tool` entry point passed 6/6 tests:

- Search valid input
- Search invalid input
- Detail valid input
- Detail invalid input
- Aggregate valid input
- Aggregate invalid input

The agent safety and step-limit tests passed 2/2.