# AI Use Disclosure

1. I used an AI assistant for planning the implementation, debugging, explaining AWS/Docker/Git steps, and reviewing the assignment requirements. I personally ran the commands, created the account and repository, tested the application, and verified the outputs.

2. I independently verified the deployed application by opening its AWS ECS public IP and confirming that the webpage loaded. I also verified that all 40 nondeterminism runs returned status `ok`.

3. I detected successful results by checking the console status lines, the generated JSON files, the summary metrics, and the AWS webpage response.

4. I changed the implementation to route model calls through `src/model_client.py`, which records input, output, and total tokens. I also added `hw1_client.py`, `/stats`, cumulative totals, and `AGENT.md` bullet-only review instructions.
