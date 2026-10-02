import json
import random
import time


class RetryableToolError(Exception):
    pass


def call_with_retry(operation, max_attempts=3, base_delay=0.05):
    attempts = []

    for attempt in range(1, max_attempts + 1):
        started = time.perf_counter()

        try:
            result = operation()
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            attempts.append(
                {
                    "attempt": attempt,
                    "status": "success",
                    "elapsed_ms": elapsed_ms,
                }
            )

            return {
                "ok": True,
                "result": result,
                "attempts": attempts,
                "total_attempts": attempt,
            }

        except RetryableToolError as error:
            elapsed_ms = round(
                (time.perf_counter() - started) * 1000,
                3,
            )

            attempts.append(
                {
                    "attempt": attempt,
                    "status": "retryable_failure",
                    "error": str(error),
                    "elapsed_ms": elapsed_ms,
                }
            )

            if attempt == max_attempts:
                return {
                    "ok": False,
                    "result": None,
                    "attempts": attempts,
                    "total_attempts": attempt,
                    "error": str(error),
                }

            delay = base_delay * (2 ** (attempt - 1))
            time.sleep(delay)


class ScriptedOperation:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.position = 0

    def __call__(self):
        outcome = self.outcomes[self.position]
        self.position += 1

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


def run_demo():
    first_success = call_with_retry(
        ScriptedOperation(
            [
                {
                    "message": "first try succeeded",
                }
            ]
        )
    )

    retry_then_success = call_with_retry(
        ScriptedOperation(
            [
                RetryableToolError("temporary timeout"),
                {
                    "message": "second try succeeded",
                },
            ]
        )
    )

    all_retries_fail = call_with_retry(
        ScriptedOperation(
            [
                RetryableToolError("tool rejected request"),
                RetryableToolError("temporary timeout"),
                RetryableToolError("tool rejected request"),
            ]
        )
    )

    return {
        "first_success": first_success,
        "retry_then_success": retry_then_success,
        "all_retries_fail": all_retries_fail,
    }


def simulate_rate(rate, total=50, seed=269004):
    rng = random.Random(seed)
    records = []

    for index in range(total):
        rejected = rng.random() < rate

        if rejected:
            operation = ScriptedOperation(
                [
                    RetryableToolError("simulated rejection"),
                    {
                        "message": "recovered after retry",
                    },
                ]
            )
        else:
            operation = ScriptedOperation(
                [
                    {
                        "message": "succeeded immediately",
                    }
                ]
            )

        result = call_with_retry(operation)

        records.append(
            {
                "record_id": index + 1,
                "rate": rate,
                "result": result,
            }
        )

    return records


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))