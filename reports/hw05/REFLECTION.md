# HW5 Agent Reflection

The HW5 agent combines a local Ollama model with three read-only domain tools: vulnerability search, vulnerability detail, and vulnerability aggregation. The agent receives a natural-language request, asks the local model to select a tool, validates the requested tool through `execute_tool`, records the result, and continues until the model finishes or the maximum step limit is reached.

The most important design decision was separating model reasoning from tool execution. The model can suggest a tool call, but it cannot directly access the database. The single `execute_tool` entry point validates the tool name and inputs, returns a consistent JSON envelope, and prevents unsupported tools from running. This makes the system easier to test and safer to operate.

The safety rule blocks destructive or sensitive requests containing terms such as delete, drop, password, secret, credential, or token. The blocked-delete scenario stopped immediately without calling the database. The maximum-step test also stopped after the configured limit, preventing an uncontrolled tool loop.

The live `qwen3:8b` tests showed that local models may need multiple turns. In one run, the model initially supplied a vulnerability code where the detail tool expected a numeric ID. The agent returned an error, and the model corrected the request using the numeric ID. This demonstrates why validation and structured error responses are necessary.

The main limitation is latency: local model calls took approximately 53–66 seconds. The system is therefore suitable for controlled investigative workflows, but interactive use would benefit from a smaller model, stronger tool schemas, and clearer examples in the system prompt.