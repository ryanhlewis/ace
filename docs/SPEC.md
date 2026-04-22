# ACE Specification

ACE is a pre-execution authorization kernel for agent side effects.

## Core Rule

```text
Execute(action) only if Valid(action, lease, evidence) = permit
```

The validator returns one of three decisions:

- `permit`: execute the action.
- `deny`: do not execute; at least one predicate failed.
- `defer`: do not execute now; approval must be renewed or evidence refreshed.

## Data Model

### Action

An action is any proposed side effect represented as JSON or text.

Examples:

- send an email
- submit a form
- approve a purchase order
- create a GitHub issue
- deploy a service

ACE hashes the action before execution. If the action changes, the lease no
longer applies.

### Lease

```json
{
  "action_id": "send-approved-invoice",
  "content_hash": "sha256...",
  "approval_state": "approved",
  "expires_at": "",
  "policy_context": {},
  "requirements": [
    {
      "field": "approval_status",
      "op": "eq",
      "value": "approved",
      "message": "approval must still be active"
    }
  ]
}
```

### Evidence

```json
{
  "snapshot_id": "snapshot-17",
  "source": "workflow-db",
  "observed_at": "2026-04-22T00:00:00Z",
  "attested": true,
  "facts": {
    "approval_status": "approved"
  }
}
```

The checker reasons over evidence, not reality. Evidence collection is outside
the proof kernel.

## Predicate Operators

| operator | meaning |
|---|---|
| `eq` | actual equals expected |
| `neq` | actual does not equal expected |
| `exists` | field is present |
| `missing` | field is absent |
| `contains` | text contains value |
| `not_contains` | text does not contain value |
| `regex` | text matches regex |
| `not_regex` | text does not match regex |
| `in` | value is in allowed set |
| `not_in` | value is not in blocked set |
| `gte` | numeric actual is greater than or equal |
| `lte` | numeric actual is less than or equal |

## Validation Algorithm

```text
if hash(action) != lease.content_hash:
    deny
elif lease.approval_state != "approved":
    deny
elif lease.expires_at has passed:
    defer
elif any predicate fails on evidence.facts:
    deny
else:
    permit
```

## Safety Claim

Assume:

- every side-effecting tool call passes through ACE
- the validator is sound for the lease language
- the evidence snapshot is the intended source of truth

Then ACE cannot increase invalid side-effect execution. It executes only the
subset of proposed actions that pass the lease.

This is a runtime shield theorem, not a claim that the LLM is always correct.
