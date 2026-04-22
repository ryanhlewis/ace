from ace_runtime.lease import Evidence, Predicate, compile_lease, validate_lease


def main() -> None:
    action = {
        "type": "publish_notice",
        "project": "Harbor Yard redevelopment",
        "channel": "city-website",
    }
    lease = compile_lease(
        action_id="publish-harbor-yard-notice",
        action=action,
        requirements=[
            Predicate("public_comment_open", "eq", True),
            Predicate("notice_hash", "eq", "notice-44"),
            Predicate("project", "eq", "Harbor Yard redevelopment"),
        ],
    )

    current_evidence = Evidence(
        facts={
            "public_comment_open": False,
            "notice_hash": "notice-44",
            "project": "Harbor Yard redevelopment",
        }
    )
    result = validate_lease(lease, current_evidence, action)
    print(result)


if __name__ == "__main__":
    main()
