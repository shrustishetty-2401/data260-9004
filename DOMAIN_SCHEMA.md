# Domain Schema
## Assigned Domain

Open-source package vulnerabilities

## Entity

Open-Source Package Vulnerability Report

## Fields

| Field | Data type | Required | Purpose and validation |
|---|---|---|---|
| vulnerabilityTitle | Text | Yes | A short title identifying the vulnerability |
| packageName | Text | Yes | The name of the affected open-source package |
| submitterEmail | Email | Yes | The Email address of the person submitting the report |
| description | Text | Yes | Details about the vulnerability; must contain more than 25 characters |
| category | Text | Yes | One of the four approved vulnerability categories |
| termsAccepted | Boolean | Yes | must be true before the form is successfully submitted |
| submissionDate | Date and time | Generated | Added by JavaScript after successful validation |

## Category Values

- Remote Code Execution
- Privilege Escalation
- Information Disclosure
- Denial of Service

