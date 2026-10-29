# DATA-260 Homework 8

GitHub repository: https://github.com/shrustishetty-2401/data260-9004

## Student and Configuration

- Student: Shrusti Shetty
- SID4: 9004
- PORT_BASE: 8004
- PREFIX: `s9004`
- SEED: 9004
- VERIFY_SEED: 269004
- DOMAIN_ID: 4
- Hardware: MacBook Pro, Apple Silicon
- Local model: `qwen3:8b`
- Final branch: `hw8`
- Final tag: `hw8`
Final tagged commit: `701d86691fb7f53273388130b1569b3d62da11d4`

## Part 1: Kafka Vulnerability Request/Response Service

The primary domain entity is `Vulnerability`.

The worker stores entities in an in-memory dictionary. Clients communicate with the worker only through Kafka.

### Kafka Topics

- `s9004_vulnerability_requests`
- `s9004_vulnerability_responses`

### Request Schema

```json
{
  "correlation_id": "unique-request-id",
  "reply_to": "s9004_vulnerability_responses",
  "operation": "CREATE_VULNERABILITY",
  "data": {
    "vulnerability_code": "HW8-DEMO-001",
    "vulnerability_title": "Kafka demonstration vulnerability",
    "package_name": "package-0",
    "submitter_email": "student@example.com",
    "description": "A sufficiently long vulnerability description.",
    "category": "Input Validation",
    "terms_accepted": true
  }
}
```

### Response Schemas

Successful CREATE responses return the generated UUID:

```json
{
  "correlation_id": "same-request-id",
  "success": true,
  "entity_id": "uuid",
  "message": "Entity created"
}
```

Successful GET responses return the complete entity:

```json
{
  "correlation_id": "same-request-id",
  "success": true,
  "entity": {
    "entity_id": "generated-uuid",
    "vulnerability_code": "HW8-DEMO-001",
    "vulnerability_title": "Kafka demonstration vulnerability",
    "package_name": "package-0",
    "submitter_email": "student@example.com",
    "description": "A sufficiently long vulnerability description.",
    "category": "Input Validation",
    "terms_accepted": true
  }
}
```

Error responses preserve the correlation ID and include an error message:

```json
{
  "correlation_id": "same-request-id",
  "success": false,
  "error": "Entity not found"
}
```

### Functionality

- CREATE vulnerability requests
- GET vulnerability requests
- UUID entity identifiers
- Correlation IDs preserved in every response
- Input validation
- Unknown-operation errors
- Missing-entity errors
- Duplicate correlation handling

The CREATE then GET demonstration succeeded. The GET request returned the created vulnerability entity, and correlation IDs were preserved.

![Part 1 service evidence](evidence/part1_services.png)

![Part 1 CREATE and GET evidence](evidence/part1_create_get.png)

Evidence:

- `raw/part1_create_get.log`
- `raw/part1_error_tests.json`
- `raw/part1_services.log`
- `raw/part1_worker_full.log`
- `raw/part1_demo_full.log`

### FastAPI Health Evidence

The API listens on `0.0.0.0:8004` inside Docker so that the container port is reachable. From the host, the service was verified through `http://127.0.0.1:8004/health` and returned HTTP 200.

### Part 1 Implementation Evidence

![Kafka client implementation](evidence/part1_code_client.png)

![Homework demo implementation](evidence/part1_code_demo.png)

![Kafka worker implementation](evidence/part1_code_worker.png)

![API wrapper implementation](evidence/part1_code_api.png)

![Complete worker message flow](evidence/part1_worker_full.png)

![Complete client message flow](evidence/part1_demo_full.png)

![FastAPI health check](evidence/part1_health.png)

## Part 2: Multi-Agent Kafka Pipeline

Implemented separate Planner, Writer, and Reviewer processes.

### Kafka Topics

- `s9004_inbox`
- `s9004_tasks`
- `s9004_drafts`
- `s9004_final`

### Agent Responsibilities

- Planner receives the question and creates a plan.
- Writer creates an answer draft.
- Reviewer evaluates the draft.
- Approved results are published to the final topic.

The pipeline completed successfully with status `approved`. The task ID and correlation ID were preserved through the pipeline.

### Coordination Explanation

Kafka coordinates the agents through independent topics. The Planner publishes a plan to `s9004_tasks`, the Writer publishes a draft to `s9004_drafts`, and the Reviewer publishes the approved result to `s9004_final`. Task IDs and correlation IDs connect the stages without requiring the agents to run in one process.

![Part 2 pipeline evidence](evidence/part2_pipeline.png)
![Complete Planner, Writer, and Reviewer pipeline](evidence/part2_full_pipeline.png)


Evidence:

- `raw/part2_pipeline_result.json`
- `raw/part2_pipeline.log`
- `RUN_LOG.txt`
- `raw/part2_planner_full.log`
- `raw/part2_writer_full.log`
- `raw/part2_reviewer_full.log`
- `raw/part2_sender_full.log`

For the same task, the Planner received the question and sent a plan to `s9004_tasks`; the Writer received that plan and sent a draft to `s9004_drafts`; and the Reviewer received the draft and sent the approved result to `s9004_final`. The task ID `389c9797-34ab-4de6-8545-046dfb50da47` and correlation ID `5017368c-5c7a-4048-87ca-c80056795513` were preserved across all stages.


## Part 3: Reliability, Failure Handling, and Ordering

### Duplicate Delivery and Idempotency

The same CREATE request was delivered twice. Both responses returned the same entity ID.

- `same_entity_id`: `true`
- `duplicate_prevented`: `true`

Evidence:

- `raw/duplicate_delivery.json`

### Consumer Death and Recovery

### Consumer Restart Evidence

The Writer was killed while processing task `b7bbc560-49e1-41f3-a711-158351720305`. After restart, Kafka redelivered the uncommitted task. The Writer completed the task, published the draft, committed the offset, and the test reported `recovered_after_restart: true`.

Evidence:

- `raw/part3_consumer_death_writer.log`
- `raw/part3_consumer_death_test.log`

The Writer was stopped during a simulated long-running task. After restarting the Writer, Kafka redelivered the uncommitted message and the task completed successfully.

- `recovered_after_restart`: `true`
- `draft_received`: `true`

Evidence:

- `raw/consumer_death.json`

Evidence:

- `raw/consumer_death.json`

![Consumer death Writer evidence](evidence/part3_consumer_death_writer.png)

![Consumer death recovery result](evidence/part3_consumer_death_test.png)

### Poison Messages and Dead-Letter Handling

Poison messages intentionally failed processing. The Writer retried each message three times and then moved it to the dead-letter topic.

- Retry limit: 3
- Dead-letter topic: `s9004_dead_letter`
- `moved_to_dead_letter`: `true`

Evidence:

- `raw/poison_message.json`

### Kafka Ordering

Twenty unkeyed and twenty keyed messages were tested.

| Case | Partitions | Order preserved |
|---|---:|---|
| Unkeyed messages | 2 | No |
| Keyed messages | 1 | Yes |

The ordering experiment used two Kafka partitions and two Writer instances in the same consumer group. Unkeyed messages were distributed across partitions and were not globally ordered. Keyed messages used the same entity key, were routed to one partition, and preserved their order.

- `keyed_order_preserved`: `true`
- Verification seed: `269004`

![Part 3 failure and ordering evidence](evidence/part3_failures.png)

Evidence:

- `raw/ordering_results.json`
- `raw/part3_failure_summary.log`
- `raw/ordering_writer_a.log`
- `raw/ordering_writer_b.log`
- `raw/part3_writer_failure_full.log`
- `raw/part3_poison_full.log`
- `raw/part3_after_poison_full.log`

![Writer A](evidence/part3_writer_a.png)

![Writer B](evidence/part3_writer_b.png)

![Ordering result](evidence/part3_ordering_result.png)

![Poison retry, dead-letter, and recovery](evidence/part3_poison_recovery.png)

![Writer A and Writer B processing evidence](evidence/part3_writers_processing.png)


## Kafka Reliability Conclusions

Kafka provides:

- Durable message storage
- Consumer-group coordination
- Redelivery of uncommitted messages
- Retry and dead-letter processing
- Correlation between requests and responses
- Per-key ordering through partition assignment
- Decoupling between independent services

The producer is responsible for publishing valid messages and using stable keys when ordering matters. The consumer is responsible for validation, idempotency, retries, offset commits, and dead-letter handling.

The Writer was killed during a simulated long-running task before committing its offset. After restart, Kafka redelivered the uncommitted task. The Writer completed the task, published the draft, and committed the offset.

### Comparison with HW2

HW2 used a simpler request/response workflow. HW8 extends that design with Kafka topics, independent consumers, consumer groups, offset commits, retries, dead-letter handling, idempotency, consumer restart recovery, and key-based ordering.

Kafka adds durable asynchronous coordination, but it also requires explicit handling of commits, retries, duplicate messages, consumer failures, and ordering.

Two benefits gained from Kafka were independent scaling of agents and decoupled failure recovery. Two new responsibilities were duplicate/idempotency handling and explicit ordering and offset management.

### Failure Comparison Table

| Failure scenario | Before fix | After fix |
|---|---|---|
| Duplicate delivery | Replay could create an additional side effect. | The same entity ID was returned and the duplicate was prevented. |
| Consumer killed mid-work | Processing stopped before the offset was committed. | Restart caused redelivery and successful completion. |
| Poison message | A bad message could continue failing without bounded handling. | The message was retried three times and moved to `s9004_dead_letter`. |
| Two partitions/two consumers | Unkeyed related messages were not globally ordered. | Keyed related messages used one partition and preserved order. |

Each row is supported by the matching raw JSON or log evidence listed in the Part 3 sections above.

### Short Implementation Evidence

The worker dispatches only the two required operations:

```python
if operation == "CREATE_VULNERABILITY":
    response = create_vulnerability(data)
elif operation == "GET_VULNERABILITY":
    response = get_vulnerability(data)
else:
    response = {"success": False, "error": "Unknown operation"}
```

Every response preserves the request correlation ID:

```python
response["correlation_id"] = message["correlation_id"]
await producer.send_and_wait(reply_to, json.dumps(response).encode())
```

Poison messages use bounded retries and then move to the dead-letter topic:

```python
if retry_number >= MAX_RETRIES:
    await producer.send_and_wait(DEAD_LETTER_TOPIC, encoded_message)
    await consumer.commit()
```The Writer retries failed messages in a bounded loop:

```python
while True:
    try:
        await process_message(message, producer)
        await consumer.commit()
        break
    except Exception as error:
        attempts[attempt_key] += 1
        retry_number = attempts[attempt_key]

        if retry_number >= MAX_RETRIES:
            await producer.send_and_wait(
                DEAD_LETTER_TOPIC,
                encoded_message,
            )
            await consumer.commit()
            break

        await asyncio.sleep(1)

Ordering uses the related entity as the Kafka message key:

```python
key = b"vulnerability-42"
await producer.send_and_wait(TASKS_TOPIC, payload, key=key)
```

### AI Use

1. AI assistance was used for drafting Kafka client, worker, multi-agent, retry, dead-letter, ordering, verification, and report code. The student ran the commands, inspected the outputs, captured the evidence, and made the final repository changes.
2. One initial AI-produced design created the Kafka producer outside an asynchronous function, which failed with a Python 3.13 event-loop error. Another initial retry design waited for Kafka redelivery instead of retrying poison messages immediately.
3. These problems were detected by running the Docker service and poison-message tests. The API failed during startup in the first case, and the poison test timed out in the second case.
4. The producer and consumer objects were moved into the asynchronous startup method. The Writer was changed to retry in a bounded loop, send the message to `s9004_dead_letter` after three failures, and commit the offset only after dead-letter publication.

## Reproducibility Evidence

- `RUN_LOG.txt`
- `METRICS.md`
- `AI_USE.md`
- `verification.json`
- `raw/part1_create_get.log`
- `raw/part1_error_tests.json`
- `raw/part1_services.log`
- `raw/part2_pipeline_result.json`
- `raw/part2_pipeline.log`
- `raw/duplicate_delivery.json`
- `raw/consumer_death.json`
- `raw/poison_message.json`
- `raw/ordering_results.json`
- `raw/part3_failure_summary.log`
- `raw/part1_worker_full.log`
- `raw/part1_demo_full.log`
- `raw/part2_planner_full.log`
- `raw/part2_writer_full.log`
- `raw/part2_reviewer_full.log`
- `raw/part2_sender_full.log`
- `raw/part3_writer_failure_full.log`
- `raw/part3_poison_full.log`
- `raw/part3_after_poison_full.log`
- `raw/ordering_writer_a.log`
- `raw/ordering_writer_b.log`

## Final Verification

The verification script reported:

- API health: passed
- Part 1 CREATE/GET evidence: passed
- Part 1 error tests: passed
- Part 2 pipeline approval: passed
- Duplicate delivery prevention: passed
- Consumer death recovery: passed
- Poison dead-letter handling: passed
- Keyed ordering preservation: passed
- Required evidence directory: passed

Overall result: `all_passed: true`

The final `verification.json` reported `all_passed: true` for API health, CREATE/GET evidence, error tests, pipeline approval, duplicate prevention, consumer recovery, dead-letter handling, keyed ordering, and the required evidence directory.

{
  "homework": "DATA-260 Homework 8",
  "sid4": 9004,
  "commit_hash": "688891208660e40cb943af9927e0dd04f73ad9af",
  "model": "qwen3:8b",
  "port_base": 8004,
  "prefix": "s9004",
  "seed": 9004,
  "verify_seed": 269004,
  "domain_id": 4,
  "checks": {
    "api_health": true,
    "part1_create_get_evidence": true,
    "part1_error_tests": true,
    "part2_pipeline_approved": true,
    "duplicate_delivery_prevented": true,
    "consumer_death_recovered": true,
    "poison_dead_letter": true,
    "keyed_ordering_preserved": true,
    "required_evidence_directory": true
  },
  "all_passed": true
}

### Verification JSON

The complete machine-readable verification output is stored in:

- `verification.json`

It records the homework name, SID4, commit hash, model, port configuration, seeds, domain ID, all verification checks, and the final `all_passed` result.


## Submission Files

The final HW8 report is available here:

[Open the final HW8 report PDF on GitHub](https://github.com/shrustishetty-2401/data260-9004/blob/hw8/reports/hw08/Shetty_HW8.pdf)

Local repository path:

`reports/hw08/Shetty_HW8.pdf`