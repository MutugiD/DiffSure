# Challenge Context

## Source problem

The client sends an HTTP service a base64-encoded `tar.gz` Git repository, a
natural-language change request, a request identifier, and a deadline. The
service must return a unified diff before that deadline. The client applies the
diff to an untouched snapshot and evaluates it with private tests inside an
offline, resource-limited environment.

Acceptance is binary. A late, malformed, non-applying, or behaviorally wrong
patch receives no credit. A null diff is allowed so the service can fail closed
instead of returning unverified output.

## Supplied environment

The public corpus covers Python, JavaScript, Bash, Go, and C. The stated private
matrix also includes Rust and Java. One Ubuntu 24.04 acceptance image contains
all required toolchains. Every supplied repository exposes `run_tests.sh` at
its root.

## Contract discrepancy

The prose asks the service to use `test_command` from `task.json`, but the HTTP
payload and packed repository do not include that file. DiffSure therefore uses
the executable contract present in every snapshot: `bash run_tests.sh`. The
architecture records this as an explicit fail-closed decision.

## Product boundary

DiffSure is the patch-producing service, not the grading harness. It does not
read private acceptance files, search outside the received snapshot, execute
candidate code on the host, or claim that generated tests prove hidden-test
correctness.
