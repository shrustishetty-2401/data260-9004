# DATA-260 Homework 1

Repository: `data260-9004`

## Configuration

- SID4: 9004
- PORT_BASE: 8004
- PREFIX: s9004
- SEED: 9004
- VERIFY_SEED: 269004
- DOMAIN_ID: 4
- Domain: Open-source package vulnerabilities

## Run locally

```bash
docker build -t data260-9004-hw1 .
docker run --rm -p 8004:80 data260-9004-hw1
