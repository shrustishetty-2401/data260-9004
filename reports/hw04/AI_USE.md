# AI Use Disclosure

## 1. What AI was used for

AI was used to help plan the HW4 implementation, explain the assignment requirements, suggest file organization, draft starter code, explain React/FastAPI/MySQL concepts, and help debug errors.

The student performed the commands, installed the dependencies, ran the application, tested the endpoints, checked the database results, ran the benchmarks, reviewed the outputs, and made the final decisions.

## 2. Incorrect or unsuitable AI output

During development, the seeded related-item code initially selected vulnerability IDs from `1` through `5000`. This failed because the database IDs did not start at exactly 1 after earlier test records had been created.

The RAG program also initially failed because some retrieved chunks did not contain a `source_number` field.

## 3. How the problems were detected

The problems were detected by reading the Python traceback and checking the database contents.

The database error showed a foreign-key constraint failure. The RAG error showed:

```text
KeyError: 'source_number'