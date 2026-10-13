# Agent Instructions

## Project Description

- This project tracks open-source package vulnerabilities.
- HW6 adds MongoDB document storage, conversational memory, memory-cost experiments, and file-based memory.

## Technology Stack

- Use Python and FastAPI for backend services.
- Use MongoDB and PyMongo for HW6 document and memory collections.
- Use the existing SQLAlchemy database for the previous homework features.
- Use the existing local Ollama adapter with the `qwen3:8b` model.
- Use React and Vite for the existing frontend.

## Coding Conventions

- Use type hints for new Python functions and data structures.
- Use Pydantic schemas for request validation.
- Keep database connections and collections in dedicated modules.
- Keep FastAPI route handlers in router modules.
- Use UTC timestamps for stored records.
- Return clear HTTP status codes and error messages.
- Keep secrets and local connection strings in `.env`.

## Testing Approach

- Run `python -m py_compile` after changing Python files.
- Test FastAPI endpoints with curl or Postman.
- Test successful, invalid, and not-found API requests.
- Verify MongoDB collections and documents directly.
- Save reproducible experiment results under `reports/hw06/raw/`.
- Record commands, timestamps, and outcomes in `reports/hw06/RUN_LOG.txt`.

## Prohibited Actions

- Do not delete or overwrite previous homework application code.
- Do not change the existing SQL database schema unless explicitly required.
- Do not commit passwords, API keys, or private connection strings.
- Do not silently ignore validation errors or contradictory memory facts.
- Do not create a separate copy of the application for HW6.
- Do not claim an experiment passed without recording its actual result.

## Code Review Format

- For code reviews, respond using strict bullet points only.
- Every non-empty response line must begin with `-`.
- Identify correctness issues, risks, and specific improvements.