# HW6 Memory Metrics

## Short-Term Memory Comparison

| Setting | Mean prompt tokens/turn | Mean latency (ms) | Probe quality (1-5) |
|---|---:|---:|---:|
| SHORT_TERM_N=4 | 286.97 | 5000.13 | 3.0 |
| SHORT_TERM_N=12 | 614.17 | 9255.64 | 2.8 |
| SHORT_TERM_N=30 | 1020.77 | 12746.58 | 2.8 |
| Eviction policy, N=12, max 10 episodes | 685.40 | 10635.50 | 3.0 |

## Completion Tokens and Cost Estimate

Pricing used:

- Input: $1 per million tokens
- Output: $5 per million tokens
- Workload: 10,000 conversations
- Conversation length: 30 turns

| Setting | Mean completion tokens/turn | Estimated cost for 10,000 conversations |
|---|---:|---:|
| SHORT_TERM_N=4 | 37.93 | $142.99 |
| SHORT_TERM_N=12 | 50.13 | $259.45 |
| SHORT_TERM_N=30 | 44.20 | $372.53 |
| Eviction policy, N=12 | 57.03 | $291.17 |

## Analysis

SHORT_TERM_N=4 was the best measured setting because it had the lowest prompt-token usage, lowest latency, lowest estimated cost, and a probe score of 3.0.

SHORT_TERM_N=30 was the worst measured setting because it had the highest prompt-token usage, highest latency, highest estimated cost, and a lower probe score of 2.8.

The eviction policy limited each user's stored episodic facts to the 10 most recent facts by deleting the oldest records. In this run, the eviction policy did not reduce measured cost compared with the baseline N=12 run. The eviction run used 685.40 prompt tokens per turn and cost an estimated $291.17, compared with 614.17 prompt tokens per turn and $259.45 for baseline N=12. This single-run difference may be affected by model-output variation and the additional experiment session.

Probe scores were calculated using the fixed expected-answer criteria in memory_probes.yaml.

## Raw Evidence

- `raw/experiment_short_term_4.json`
- `raw/experiment_short_term_12.json`
- `raw/experiment_short_term_30.json`
- `raw/experiment_eviction_12.json`
- `raw/chat_metrics.jsonl`
- `memory_probes.yaml`