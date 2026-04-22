# Limitations

ACE is a runtime control boundary. It is not a complete agent safety system.

## Policy Compilation Is Critical

ACE enforces predicates. If the predicates are wrong, incomplete, or too broad,
ACE will enforce the wrong policy. Production systems need reviewed compilers,
schema tests, and regression suites for policies.

## Evidence Is Not Reality

ACE validates evidence snapshots. It does not prove the world. If evidence is
false, stale, forged, or incomplete, the decision can be wrong.

Recommended production controls:

- evidence provenance
- freshness checks
- signed or attested snapshots
- source-specific trust levels
- logs linking decisions to evidence ids

## Side-Effect Mediation Is Required

The guarantee only holds if every side-effect channel is mediated by ACE. If an
agent can call tools directly, bypass the gate, or mutate state after validation,
the guarantee collapses.

## Overblocking Needs Real-World Measurement

The included benchmark measures overblocking on paired policy probes. Real
systems contain vague policies, missing evidence, and conflicting goals.
Production deployments should track:

- false block rate
- re-approval burden
- latency cost
- user override frequency
- blocked action explanations

## Not A General Reasoning Benchmark

ACE should not be evaluated primarily on MMLU-style question answering. The
runtime matters when an agent acts on the world under explicit assumptions,
permissions, and policies.
