# Security

ACE is a control boundary for side effects, but it is not a sandbox by itself.

Production deployments should ensure:

- all side-effecting tools are mediated by ACE
- evidence snapshots have provenance and freshness checks
- receipts are logged for every permit, deny, and defer decision
- actions cannot change after validation without revalidation
- policies and lease compilers are tested against regression fixtures

Do not store secrets in leases, benchmark artifacts, or public evidence files.
