# DATA-260 Homework 7

## Student and Configuration

- Student: Shrusti Shetty
- SID4: 9004
- Port base: 8004
- Prefix: `s9004`
- Domain ID: 4
- Seed: 9004
- Verify seed: 269004
- Branch: `hw6`
- Final tag: `hw7`

## Part 1: JWT Authentication and Roles

Implemented JWT authentication with MySQL-backed users.

Test users:

- `reader` / `data260`
- `writer` / `data260`
- `moderator` / `data260`

Verified:

- Successful login returns a JWT.
- Missing token returns HTTP 401.
- Invalid credentials return HTTP 401.
- Reader package creation returns HTTP 403.
- Writer package creation returns HTTP 201.
- Writer package deletion returns HTTP 403.
- Moderator package deletion returns HTTP 200.

Ruff and pre-commit checks passed.

## Part 2: Tool-Using Agent

Implemented a tool-using agent with:

- `search_vulnerabilities`
- `vulnerability_detail`
- `vulnerability_aggregate`

The agent supports:

- Multiple tool calls.
- Tool-role messages.
- Input validation.
- Malformed-argument repair.
- Unknown-tool blocking.
- Maximum-step limits.
- Safe handling of nonexistent vulnerability IDs.

Evidence:

- `raw/agent_reliability.json`
- `RUN_LOG.txt`

## Part 3: Reflexion

Implemented a Reflexion workflow with:

- Deterministic verification.
- Reflection after failed attempts.
- Revised strategy.
- Maximum two retries.
- Tool and token budgets.
- Stored reflection evidence.

Results:

- Original successful tasks: 2
- Reflexion successful tasks: 3
- Original retry rate: 0.000
- Reflexion retry rate: 0.333
- Verifier false rejections: 0

Evidence:

- `raw/reflexion_comparison.json`
- `raw/reflections.json`

## Part 4: Bike-Share ReAct/MRKL Application

Implemented a React/Vite bike-share decision application.

Tools:

1. `csv_sql`
2. `policy_retriever`
3. `calculator`

The application displays:

- Uploaded CSV filename.
- Tool execution timeline.
- Weekly comparison table.
- Membership or pay-per-use decision.
- Pricing source.
- Pricing snapshot SHA-256 hash.
- Completion stop reason.

Datasets:

| Dataset | Rows | Member rides | Casual rides | Result |
|---|---:|---:|---:|---|
| `bikeshare_membership_wins.csv` | 800 | 700 | 100 | Membership is stronger |
| `bikeshare_pay_per_use_wins.csv` | 800 | 100 | 700 | Pay-per-use is stronger |

Screenshots:

- `evidence/part4_membership_wins.png`
- `evidence/part4_pay_per_use_wins.png`

Pricing evidence:

- `raw/pricing_snapshot.txt`
- `raw/pricing_snapshot.sha256`

## Part 5: Prompt-Injection Defense

Tested three attacks:

- Instruction override.
- Unauthorized tool abuse.
- CSV-based prompt injection.

Results:

- Attack cases: 3
- Defended cases: 3
- Defense success rate: 100%

Evidence:

- `raw/prompt_injection_results.json`

## Part 6: File Tools and Safety

Implemented safe file tools for the approved HW7 directory.

Verified:

- File listing works.
- File reading works.
- Unconfirmed writes are blocked.
- Path traversal is blocked.

Evidence:

- `raw/file_tools_results.json`

## Reproducibility Evidence

- `RUN_LOG.txt`
- `METRICS.md`
- `AI_USE.md`
- `verification.json`
- `raw/agent_reliability.json`
- `raw/reflexion_comparison.json`
- `raw/reflections.json`
- `raw/prompt_injection_results.json`
- `raw/file_tools_results.json`

## Final Verification

The following checks passed:

- Python compilation.
- Ruff check.
- Pre-commit hooks.
- Backend API startup.
- JWT authentication tests.
- Role-permission tests.
- Agent tests.
- Tool tests.
- Reliability experiments.
- Reflexion experiments.
- Bike-share API test.
- React production build.
- Prompt-injection tests.
- File-safety tests.

Final commit and tag will be recorded after the completed report is committed.