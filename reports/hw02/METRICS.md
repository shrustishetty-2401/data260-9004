# DATA-260 Homework 2 Metrics

## Configuration

- SID4: 9004
- PORT_BASE: 8004
- PREFIX: s9004
- SEED: 9004
- VERIFY_SEED: 269004
- DOMAIN_ID: 4
- Model: qwen3:8b
- Deployment turn ceiling: 2

## Schema Validation Experiment

Frozen input:

`reports/hw02/cases/schema_input.json`

| Outcome | Count | Mean latency |
|---|---:|---:|
| Valid first attempt | 30 | 2375.73 ms |
| Valid after 1 retry | 0 | N/A |
| Valid after 2+ retries | 0 | N/A |
| Hit turn ceiling | 0 | N/A |

Completion rate: 100%

## Turn Ceiling Comparison

| Turn ceiling | Runs | Completion rate | Mean latency |
|---:|---:|---:|---:|
| 2 | 20 | 100% | 2342.93 ms |
| 10 | 20 | 100% | 2350.98 ms |

### Deployment choice

I selected a turn ceiling of 2 because both configurations completed all 20 runs, while ceiling 2 had lower mean latency.

## Adversarial Experiment

Input:

`reports/hw02/cases/adversarial_input.json`

| Outcome | Count |
|---|---:|
| Valid first attempt | 0 |
| Valid after 1 retry | 0 |
| Valid after 2+ retries | 0 |
| Hit turn ceiling | 5 |

Completion rate: 0%

Mean latency: 7390.14 ms

The adversarial input instructed the model to violate the required output format. The generated summary exceeded 25 words, which Pydantic correctly rejected. The retry also failed, so all five runs reached the turn ceiling.

Proposed fix: Add a deterministic final repair step that trims an overlong summary to 25 words after recording the original validation failure. This would preserve validation evidence while preventing an otherwise usable result from being abandoned.