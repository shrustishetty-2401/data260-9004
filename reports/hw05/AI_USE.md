# AI Use

## 1. What was AI used for, and what did I do myself?

AI was used for debugging support, code organization, explanations, and troubleshooting. I personally ran the terminal commands, activated the conda environment, migrated and inspected the database, tested the FastAPI package endpoints, built the React frontend, tested MCP Inspector tools, ran the retry benchmark, ran the offline tests, started Ollama scenarios, and reviewed the generated JSONL and JSON artifacts.

## 2. Was any AI-produced output wrong or unsuitable?

Yes. An early MCP setup assumed that the `mcp` package and `uv` command were already available in the active environment. This was unsuitable because the first Inspector attempt failed with missing-package and missing-command errors. I independently read the terminal errors, activated the correct `data260` environment, installed the compatible MCP version and `uv`, and reran the Inspector until the tools connected successfully.

## 3. What was independently verified?

I independently verified the database migration, package CRUD responses, React production build, MCP tool responses, invalid-input envelopes, retry scenarios, 150 benchmark records, six execute_tool tests, two agent safety tests, Ollama model availability, four agent scenarios, and the saved metrics and log files.

## 4. How was the result checked?

I compared the implementation with every HW5 requirement, ran Python compilation checks, inspected terminal outputs, tested valid and invalid requests in MCP Inspector, checked JSON and JSONL files, verified the number of benchmark records, and reviewed the final artifacts before preparing the report.