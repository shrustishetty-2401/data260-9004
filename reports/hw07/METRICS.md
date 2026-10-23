# HW7 Metrics

## Part 2: Agent Reliability

| Mode | Attempts | Well-formed calls | Well-formed rate | Successful tasks | Task success rate | Mean latency |
|---|---:|---:|---:|---:|---:|---:|
| Before repair | 10 | 7 | 70% | 3 | 30% | 12175.44 ms |
| After repair | 10 | 7 | 70% | 7 | 70% | 14851.52 ms |

Repair changed malformed-argument failures from 4 to 0 and increased task success from 30% to 70%.

## Part 3: Reflexion

| Metric | Original | Reflexion |
|---|---:|---:|
| Successful tasks | 2 | 3 |
| Retry rate | 0.000 | 0.333 |
| Tool calls | 5 | 7 |
| Estimated tokens | 2278 | 3506 |
| Latency | 41793.48 ms | 61113.38 ms |

The deterministic verifier recorded zero false rejections.

## Part 4: Bike-Share ReAct/MRKL

| Scenario | Rows | Member rides | Casual rides | Result |
|---|---:|---:|---:|---|
| Membership wins | 800 | 700 | 100 | Membership is the stronger starting option |
| Pay-per-use wins | 800 | 100 | 700 | Pay-per-use is the stronger starting option |

Tools executed:

1. `csv_sql`
2. `policy_retriever`
3. `calculator`

## Part 5: Prompt Injection

- Attack cases: 3
- Defended cases: 3
- Defense success rate: 100%

## Part 6: File Safety

- File listing: passed
- File reading: passed
- Unconfirmed write: blocked
- Path traversal: blocked