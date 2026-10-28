# AI Use

## 1. What AI assistance was used for

AI assistance was used to help interpret the HW8 requirements, plan the Kafka architecture, draft initial Python files, identify required topics and message fields, and troubleshoot runtime errors.

I personally ran the commands, started Docker and Kafka, managed the terminal processes, checked the logs, captured the evidence, and verified the results.

## 2. Example of an incorrect or unsuitable output

An initial duplicate-correlation implementation reused the same correlation ID for both CREATE and GET. Because the worker correctly used correlation IDs for idempotency, GET returned the cached CREATE response instead of retrieving the entity.

The initial poison-message implementation also counted retries only when Kafka redelivered an uncommitted message. That caused the poison test to wait indefinitely.

## 3. How the problems were detected

The incorrect CREATE/GET behavior was detected because the GET response contained `"message": "Entity created"` instead of an `"entity"` object.

The poison-message problem was detected when the test timed out without receiving a message from `s9004_dead_letter`. Worker logs showed only one retry, which demonstrated that immediate retry logic was missing.

## 4. What was changed and why it works

The demo was changed to use a separate correlation ID for each request while preserving each ID through its request/response flow.

The Writer was changed to retry failed messages immediately up to three times. After the third failure, it publishes the message to `s9004_dead_letter` and commits the offset so the poison message cannot block later messages.

The final tests confirmed successful CREATE/GET behavior, duplicate prevention, consumer restart recovery, dead-letter routing, and keyed partition ordering.