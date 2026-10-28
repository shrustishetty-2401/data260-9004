# DATA-260 Homework 8 Metrics

## Configuration

| Value | Result |
|---|---|
| SID4 | 9004 |
| PORT_BASE | 8004 |
| PREFIX | s9004 |
| SEED | 9004 |
| VERIFY_SEED | 269004 |
| DOMAIN_ID | 4 |
| Local model | qwen3:8b |

## Part 1

| Check | Result |
|---|---|
| CREATE_VULNERABILITY | Passed |
| GET_VULNERABILITY | Passed |
| UUID entity ID generated | Passed |
| Correlation ID preserved | Passed |
| Unknown operation rejected | Passed |
| Unknown entity rejected | Passed |
| Invalid fields rejected | Passed |
| Request topic | s9004_vulnerability_requests |
| Response topic | s9004_vulnerability_responses |

## Part 2

| Check | Result |
|---|---|
| Planner process | Passed |
| Writer process | Passed |
| Reviewer process | Passed |
| Four-stage Kafka flow | Passed |
| Final status | approved |
| Correlation ID preserved | Passed |
| Final topic | s9004_final |

## Part 3

| Failure scenario | Result |
|---|---|
| Duplicate delivery | Same entity ID returned; duplicate prevented |
| Consumer killed mid-work | Task recovered after Writer restart |
| Poison message | Retried 3 times and moved to s9004_dead_letter |
| Unkeyed two-partition run | Used partitions 0 and 1; order was not globally preserved |
| Keyed two-partition run | All messages stayed on one partition |
| Keyed ordering | Sequences 1 through 20 preserved |
| VERIFY_SEED | 269004 |