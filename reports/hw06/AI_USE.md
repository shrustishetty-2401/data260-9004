# AI Use

## 1. What AI Assisted With

I used an AI assistant to help plan and implement the HW6 work, including:

- Designing the MongoDB document schema for vulnerabilities.
- Creating FastAPI CRUD routes and Pydantic validation schemas.
- Implementing short-term, long-term, and episodic memory.
- Creating the memory-cost experiment runner.
- Designing the file-based AGENT.md and MEMORY.md workflow.
- Explaining terminal commands and helping interpret test results.

I personally ran the commands, started MongoDB and Ollama, inspected the outputs, tested the API, and verified the experiment results.

## 2. Incorrect or Unsuitable AI Output

The first implementation of the `/api/memory/{user_id}` endpoint returned MongoDB `ObjectId` values directly in the response. FastAPI could not serialize these values to JSON.

## 3. How I Detected the Problem

The endpoint returned an Internal Server Error. The Uvicorn traceback showed:

```text
ValueError: [TypeError("'ObjectId' object is not iterable"),
TypeError('vars() argument must have __dict__ attribute')]