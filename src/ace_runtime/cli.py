"""Command-line interface for ACE Runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ace_runtime.lease import (
    Evidence,
    Predicate,
    compile_lease,
    evidence_from_dict,
    lease_from_dict,
    lease_to_dict,
    result_to_dict,
    validate_lease,
)
from ace_runtime.stwebagentbench import download_public_stwebagentbench, run_preflight_benchmark


def main() -> None:
    parser = argparse.ArgumentParser(description="ACE Runtime: assumption-carrying execution leases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo", help="Run a minimal stale-approval demo.")
    demo.add_argument("--json", action="store_true", help="Print machine-readable JSON.")

    validate = subparsers.add_parser("validate", help="Validate an action against a lease and evidence snapshot.")
    validate.add_argument("--lease", type=Path, required=True)
    validate.add_argument("--evidence", type=Path, required=True)
    validate.add_argument("--action", type=Path, required=True)

    bench = subparsers.add_parser(
        "benchmark-stwebagentbench",
        help="Run the ST-WebAgentBench-derived ACE preflight benchmark.",
    )
    bench.add_argument("--data", type=Path, default=Path("data") / "stwebagentbench" / "test.raw.json")
    bench.add_argument("--download-if-missing", action="store_true")
    bench.add_argument("--output-dir", type=Path, default=Path("results") / "stwebagentbench-ace-preflight")

    args = parser.parse_args()

    if args.command == "demo":
        result = run_demo()
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(f"valid evidence: {result['valid']['decision']} ({result['valid']['reason_code']})")
            print(f"stale evidence: {result['stale']['decision']} ({result['stale']['reason_code']})")
    elif args.command == "validate":
        lease = lease_from_dict(json.loads(args.lease.read_text(encoding="utf-8")))
        evidence = evidence_from_dict(json.loads(args.evidence.read_text(encoding="utf-8")))
        action = json.loads(args.action.read_text(encoding="utf-8"))
        print(json.dumps(result_to_dict(validate_lease(lease, evidence, action)), indent=2, sort_keys=True))
    elif args.command == "benchmark-stwebagentbench":
        if args.download_if_missing and not args.data.exists():
            download_public_stwebagentbench(args.data)
        summary = run_preflight_benchmark(args.data, args.output_dir)
        print(json.dumps(summary["pipelines"], indent=2, sort_keys=True))


def run_demo() -> dict[str, object]:
    action = {
        "type": "send_email",
        "to": "vendor@example.com",
        "subject": "Approved invoice",
    }
    lease = compile_lease(
        action_id="send-approved-invoice",
        action=action,
        requirements=[
            Predicate("approval_status", "eq", "approved", "approval must still be active"),
            Predicate("recipient", "eq", "vendor@example.com", "recipient must match approval"),
            Predicate("invoice_hash", "eq", "inv-17", "invoice content must not change"),
        ],
        policy_context={"source": "demo"},
    )
    valid = validate_lease(
        lease,
        Evidence(
            facts={
                "approval_status": "approved",
                "recipient": "vendor@example.com",
                "invoice_hash": "inv-17",
            },
            snapshot_id="valid-demo",
        ),
        action,
    )
    stale = validate_lease(
        lease,
        Evidence(
            facts={
                "approval_status": "revoked",
                "recipient": "vendor@example.com",
                "invoice_hash": "inv-17",
            },
            snapshot_id="stale-demo",
        ),
        action,
    )
    return {
        "lease": lease_to_dict(lease),
        "valid": result_to_dict(valid),
        "stale": result_to_dict(stale),
    }


if __name__ == "__main__":
    main()
