# HW4 Metrics

## N+1 Benchmark

The benchmark tested two implementations:

- Naive: one query for the reports plus one related-item query per report.
- Fixed: eager loading using `selectinload`, reducing the work to two SQL statements.

Each configuration ran 30 requests.

| Mode | Page size | SQL statements/request | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---:|---:|---:|
| Naive | 10 | 11 | 9.721 | 85.905 | 146.621 |
| Naive | 50 | 51 | 23.321 | 172.330 | 186.384 |
| Naive | 200 | 201 | 61.721 | 205.475 | 241.548 |
| Fixed | 10 | 2 | 6.858 | 59.823 | 102.780 |
| Fixed | 50 | 2 | 7.106 | 40.666 | 105.170 |
| Fixed | 200 | 2 | 11.586 | 101.521 | 132.936 |

The naive implementation grows from 11 to 201 SQL statements as page size increases. The fixed implementation remains at two SQL statements per request.

## Index Experiment

Before adding the index, MySQL used a table scan for `submitter_email`.

After creating:

```sql
CREATE INDEX idx_vulnerabilities_submitter_email
ON vulnerabilities (submitter_email);