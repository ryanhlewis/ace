from ace_runtime.lease import Evidence, Predicate, compile_lease, validate_lease


def test_lease_permits_when_evidence_matches() -> None:
    action = {"type": "send_email", "to": "vendor@example.com"}
    lease = compile_lease(
        action_id="send",
        action=action,
        requirements=[Predicate("approval_status", "eq", "approved")],
    )
    result = validate_lease(lease, Evidence(facts={"approval_status": "approved"}), action)
    assert result.decision == "permit"


def test_lease_denies_when_assumption_breaks() -> None:
    action = {"type": "send_email", "to": "vendor@example.com"}
    lease = compile_lease(
        action_id="send",
        action=action,
        requirements=[Predicate("approval_status", "eq", "approved")],
    )
    result = validate_lease(lease, Evidence(facts={"approval_status": "revoked"}), action)
    assert result.decision == "deny"
    assert result.reason_code == "predicate_failed"


def test_lease_denies_when_action_changes() -> None:
    action = {"type": "send_email", "to": "vendor@example.com"}
    lease = compile_lease(
        action_id="send",
        action=action,
        requirements=[Predicate("approval_status", "eq", "approved")],
    )
    changed = {"type": "send_email", "to": "other@example.com"}
    result = validate_lease(lease, Evidence(facts={"approval_status": "approved"}), changed)
    assert result.decision == "deny"
    assert result.reason_code == "action_hash_mismatch"


def test_list_not_in_predicate_checks_each_item() -> None:
    action = {"fields": ["ACE_HALLUCINATED_VALUE"]}
    lease = compile_lease(
        action_id="fill",
        action=action,
        requirements=[Predicate("fields", "not_in", ["ACE_HALLUCINATED_VALUE"])],
    )
    result = validate_lease(lease, Evidence(facts=action), action)
    assert result.decision == "deny"
