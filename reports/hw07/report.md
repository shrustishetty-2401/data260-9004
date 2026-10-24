# DATA-260 Homework 7

GitHub repository: https://github.com/shrustishetty-2401/data260-9004

## Student and Configuration

- Student: Shrusti Shetty
- SID4: 9004
- Port base: 8004
- Prefix: `s9004`
- Domain ID: 4
- Seed: 9004
- Verify seed: 269004
- Hardware: MacBook Pro, Apple Silicon
- Local model: `qwen3:8b`
- Branch: `hw7`
- Final tagged commit: `a3810a884db0d15a38095d3db051f89eb6396525`

## Part 1: JWT Authentication, Roles, and Linting

Implemented JWT authentication with MySQL-backed users.

Test users:

- `reader` / `data260`
- `writer` / `data260`
- `moderator` / `data260`

Verified:

- Valid login returns HTTP 200 and a JWT.
- Invalid login returns HTTP 401.
- Missing token returns HTTP 401.
- Invalid token returns HTTP 401.
- Reader package creation returns HTTP 403.
- Writer package creation returns HTTP 201.
- Writer package deletion returns HTTP 403.
- Moderator package deletion returns HTTP 200.
- Authenticated list/read request returns HTTP 200.
- Ruff and pre-commit checks pass.

### Login Evidence

![Login success and invalid login](evidence/part1_login_success_failure.png)

### Authentication Failure Evidence

![Missing and invalid token responses](evidence/part1_auth_me_401.png)

### Create Permission Evidence

![Reader 403 and writer 201 responses](evidence/part1_create_permissions.png)

### Delete Permission Evidence

![Writer 403 and moderator 200 responses](evidence/part1_delete_permissions.png)

### Authenticated Read Evidence

![Authenticated list request](evidence/part1_read_200.png)

### Linting Evidence

![Ruff and pre-commit evidence](evidence/part1_linting.png)

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

### Verification Tasks

Task A searched for a seeded vulnerability and retrieved the first result.

Task B retrieved an aggregate summary and searched for a supporting package example.

Task C searched for `package-0` and retrieved details for vulnerability IDs `10002` and `9752`.

![Tasks A, B, and C](evidence/part2_tasks_abc.png)

### Error Recovery

The nonexistent-ID test used vulnerability ID `999999999`. The tool returned `vulnerability not found`, and the agent responded without crashing.

![Nonexistent ID recovery](evidence/part2_nonexistent_id.png)

Evidence:

- `raw/agent_reliability.json`
- `RUN_LOG.txt`

## Part 3: Reflexion and Bounded Self-Correction

Implemented:

- Deterministic verification.
- Reflection after failed attempts.
- Revised strategies.
- Maximum two retries.
- Tool and token budgets.
- Stored reflection evidence.

| Metric | Original loop | Reflexion loop |
|---|---:|---:|
| Task success | 2 | 3 |
| Retry rate | 0.000 | 0.333 |
| Tool calls | 5 | 7 |
| Estimated tokens | 2278 | 3506 |
| Latency | 41793.48 ms | 61113.38 ms |
| Verifier false rejections | 0 | 0 |

![Reflexion comparison](evidence/part3_reflexion_comparison.png)

The verifier recorded zero false rejections. The stored reflections contain concise failure evidence and revised strategies without hidden chain-of-thought.

Evidence:

- `raw/reflexion_comparison.json`
- `raw/reflections.json`

## Part 4: Citi Bike ReAct/MRKL Application

Implemented a React/Vite Citi Bike decision application with the following tools:

1. `csv_sql`
2. `policy_retriever`
3. `calculator`

The application displays:

- Uploaded CSV filename.
- Tool execution timeline.
- Weekly member/casual comparison.
- Membership or pay-per-use decision.
- Pricing source.
- Pricing capture time.
- Pricing snapshot SHA-256 hash.
- Calculator output.
- Completion stop reason.

### Dataset Results

| Dataset | Rows | Member rides | Casual rides | Result |
|---|---:|---:|---:|---|
| `bikeshare_membership_wins.csv` | 800 | 700 | 100 | Membership is stronger |
| `bikeshare_pay_per_use_wins.csv` | 800 | 100 | 700 | Pay-per-use is stronger |

### Membership-Win Scenario

![Membership-win scenario](evidence/part4_membership_wins.png)

The membership-win dataset contains 700 member rides and 100 casual rides. The application selected membership because member usage was dominant.

### Pay-Per-Use-Win Scenario

![Pay-per-use-win scenario](evidence/part4_pay_per_use_wins.png)

The pay-per-use-win dataset contains 100 member rides and 700 casual rides. The application selected pay-per-use because casual usage was dominant.

Pricing evidence:

- `raw/pricing_snapshot.txt`
- `raw/pricing_snapshot.sha256`

## Part 5: Prompt-Injection Defense

### Threat Model

The threat model covers:

- Recommendation override: an attacker attempts to force an incorrect plan recommendation.
- Non-read-only tool misuse: an attacker attempts to make the SQL tool modify data.
- Data exfiltration: an attacker attempts to include restricted uploaded content in the final answer.

The hostile fixture is stored at:

- `raw/hostile_pricing_fixture.html`

Tested attacks:

- Instruction override.
- Unauthorized tool abuse.
- CSV-based prompt injection.

Results:

- Attack cases: 3
- Defended cases: 3
- Defense success rate: 100%

![Prompt-injection defense](evidence/part5_injection_defense.png)

Retrieved text is treated as untrusted data. Tool-boundary enforcement is stronger than prompt-only defense because the tool itself rejects unsafe operations even if an input attempts to bypass the instructions.

### Before-and-After Defense Results

| Attack | Before defense | After defense | Result |
|---|---|---|---|
| Instruction override | Input attempted to replace trusted instructions and expose restricted information. | Trusted policy remained active and the request was blocked. | Defended |
| Unauthorized tool abuse | Input attempted to use an approved tool for arbitrary Python execution and environment-variable access. | Tool use was restricted to approved read-only operations. | Defended |
| CSV prompt injection | Uploaded text attempted to override the pricing recommendation. | Uploaded content was treated as untrusted data and the attack was blocked. | Defended |

Overall defense result: 3 of 3 attacks were blocked successfully.

Evidence:

- `raw/prompt_injection_results.json`
- `raw/hostile_pricing_fixture.html`

## Part 6: File Tools and Safety Gate

Implemented:

- `read_file`
- `write_file`
- `edit_file`
- `glob_files`
- `search_in_files`
- `bash`

The safety gate includes:

- `SAFE_PREFIXES`
- `is_destructive`
- `confirm_bash`
- Explicit confirmation for destructive commands.
- Path traversal protection.
- Unconfirmed write protection.

The integration test performed:

```text
glob -> search -> read
```

The safety suite tested ten commands. Five safe commands were allowed and five destructive or restricted commands were blocked.

The results confirmed that file listing, file search, file reading, unconfirmed-write blocking, path-traversal blocking, and destructive-command confirmation all work as intended.

![File tools and safety evidence](evidence/part6_file_tools_safety.png)

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
- `raw/pricing_snapshot.txt`
- `raw/pricing_snapshot.sha256`
- `raw/hostile_pricing_fixture.html`
- `raw/bikeshare_membership_wins.csv`
- `raw/bikeshare_pay_per_use_wins.csv`

## Final Verification

The following checks passed:

- Python compilation.
- Ruff check.
- Pre-commit hooks.
- Backend API startup.
- JWT authentication tests.
- Invalid-login test.
- Missing-token test.
- Role-permission tests.
- Authenticated read test.
- Agent tests.
- Tool tests.
- Reliability experiment.
- Reflexion experiment.
- Bike-share API test.
- React production build.
- Prompt-injection tests.
- File-safety tests.

The final `hw7` branch and tag point to:

`a3810a884db0d15a38095d3db051f89eb6396525`

## Submission Files

The final submission PDF is:

`reports/hw07/Shetty_HW7.pdf`

The report includes screenshots for Parts 1 through 6, machine-readable experiment outputs, verification results, and reproducibility evidence.