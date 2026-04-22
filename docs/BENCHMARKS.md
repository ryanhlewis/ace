# Benchmarks

## ST-WebAgentBench-Derived Policy Preflight

The included benchmark uses public policy rows from
[ST-WebAgentBench](https://github.com/segev-shlomov/ST-WebAgentBench). Each
policy instance is compiled into two deterministic probes:

- a violating action that should be denied
- a compliant action that should be permitted

This tests whether ACE can enforce externally-defined policies before execution.
It is not the official browser leaderboard because it does not run a full web
agent inside the browser environments.

## Reproduce

```bash
ace-runtime benchmark-stwebagentbench \
  --download-if-missing \
  --data data/stwebagentbench/test.raw.json \
  --output-dir results/stwebagentbench-ace-preflight
```

## Current Result

Source snapshot:

```text
31817831f963425bdc4d582936f2b9c0b9714fc986be7b4df67e50f2921e9a34
```

| pipeline | score | violation block | overblock |
|---|---:|---:|---:|
| execute-all baseline | 3,057 / 6,114 = 50.0% | 0.0% | 0.0% |
| keyword guard baseline | 3,772 / 6,114 = 61.7% | 23.4% | 0.0% |
| ACE preflight | 6,114 / 6,114 = 100.0% | 100.0% | 0.0% |

## Why This Is Trustworthy

- The source policies are external and public.
- The benchmark logs every generated probe to `records.jsonl`.
- Each probe includes the source task id, policy template, category, action,
  expected decision, actual decision, and predicates.
- The source file hash is included in the report.
- No LLM endpoint is required to reproduce the result.

## What This Does Not Prove

This benchmark does not prove that a full browser agent achieves official
Completion under Policy. It proves the pre-execution checker can enforce policy
leases compiled from the public benchmark rows.

The next benchmark step is to insert ACE into an actual BrowserGym or
ST-WebAgentBench action loop and compare official task completion, policy
violations, and overblocking.
